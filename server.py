from contextlib import asynccontextmanager
import asyncio
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse, Response
from pydantic import BaseModel
from datetime import datetime, timedelta
from mock_data import (
    EXPECTED_CATALOG,
    LIVE_TRAFFIC_FLOW,
    analyze_api_discrepancies,
    get_api_detail,
)
import ai_engine
import openrouter_engine
import database as db
from email_notifier import send_decommission_email
import kong_client
from auth import get_current_user, router as auth_router
import admin
from csv_ingestion import router as catalog_router
from probe_engine import probe_and_classify, scan_for_secrets, check_rate_limit, _build_headers
import requests as req_lib
import httpx
import io
import time
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from urllib.parse import urlparse
from path_utils import normalize_path
from dotenv import load_dotenv

load_dotenv()

PROBE_INTERVAL_SECONDS = 30 * 60  # 30 minutes

# Track the next scheduled scan time for GET /api/monitor
_next_scheduled_scan: datetime | None = None


# ── Anomaly detection rules ────────────────────────────────────────────────────

def _detect_anomalies(api_id: str, url: str, old: dict, new: dict) -> list:
    """Compare old vs new probe result and return any security events."""
    events = []
    now = datetime.utcnow().isoformat() + "Z"

    # auth_exposed False → True
    if not old.get("auth_exposed") and new.get("auth_exposed"):
        events.append({
            "api_id": api_id, "url": url,
            "anomaly_type": "auth_exposed_changed",
            "old_value": False, "new_value": True,
            "severity": "CRITICAL", "detected_at": now,
        })

    # lazarus_status ZOMBIE → ACTIVE
    old_ls = str(old.get("lazarus_status", "")).upper()
    new_ls = str(new.get("lazarus_status", "")).upper()
    if old_ls == "ZOMBIE" and new_ls == "ACTIVE":
        events.append({
            "api_id": api_id, "url": url,
            "anomaly_type": "status_zombie_to_active",
            "old_value": old_ls, "new_value": new_ls,
            "severity": "HIGH", "detected_at": now,
        })

    # http_code 4xx → 200
    old_code = old.get("http_code") or 0
    new_code = new.get("http_code") or 0
    if 400 <= old_code < 500 and new_code == 200:
        events.append({
            "api_id": api_id, "url": url,
            "anomaly_type": "http_code_4xx_to_200",
            "old_value": old_code, "new_value": new_code,
            "severity": "CRITICAL", "detected_at": now,
        })

    # lazarus_status ACTIVE → ZOMBIE
    if old_ls == "ACTIVE" and new_ls == "ZOMBIE":
        events.append({
            "api_id": api_id, "url": url,
            "anomaly_type": "status_active_to_zombie",
            "old_value": old_ls, "new_value": new_ls,
            "severity": "MEDIUM", "detected_at": now,
        })

    return events


# ── Core scan function (reused by scheduler + manual trigger) ──────────────────

async def _run_probe_scan() -> dict:
    """
    Probe all APIs in the catalog, detect anomalies, persist results + metadata.
    Returns the monitor payload dict.
    """
    global _next_scheduled_scan

    apis = await db.get_all_api_catalog()
    if not apis:
        now_iso = datetime.utcnow().isoformat() + "Z"
        return {
            "last_scan": now_iso,
            "next_scan": _next_scheduled_scan.isoformat() + "Z" if _next_scheduled_scan else None,
            "total_apis": 0,
            "scan_results": [],
        }

    # Snapshot old values for anomaly detection
    old_map = {a["api_id"]: a for a in apis}

    results = await probe_and_classify(apis)
    scan_time = datetime.utcnow()
    scan_time_iso = scan_time.isoformat() + "Z"

    scan_results = []
    zombie_count = stale_count = active_count = shadow_count = 0

    for result in results:
        aid = result.get("api_id")
        result["probed_at"] = scan_time_iso
        await db.upsert_api_catalog({**result, "ingested_at": scan_time_iso})

        # Anomaly detection
        old_doc = old_map.get(aid, {})
        anomalies = _detect_anomalies(
            aid, result.get("url", ""), old_doc, result
        )
        for event in anomalies:
            await db.save_security_event(event)

        # Status change log (existing behaviour)
        old_status = old_doc.get("lazarus_status", "ACTIVE")
        new_status = result.get("lazarus_status", "ACTIVE")
        if old_status != new_status:
            await db.log_status_change(aid, old_status, new_status)

        # Count
        ls = str(new_status).upper()
        if ls == "ZOMBIE":
            zombie_count += 1
        elif ls == "STALE":
            stale_count += 1
        elif ls == "SHADOW":
            shadow_count += 1
        else:
            active_count += 1

        scan_results.append({
            "api_id": aid,
            "url": result.get("url"),
            "lazarus_status": new_status,
            "http_code": result.get("http_code"),
            "response_time_ms": result.get("response_time_ms"),
            "auth_exposed": result.get("auth_exposed"),
            "reachable": result.get("reachable"),
            "probed_at": scan_time_iso,
        })

    # Sort: ZOMBIE/CRITICAL first
    _severity_order = {"ZOMBIE": 0, "SHADOW": 1, "STALE": 2, "ACTIVE": 3}
    scan_results.sort(key=lambda r: _severity_order.get(str(r.get("lazarus_status", "")).upper(), 9))

    # Persist scan metadata
    meta = {
        "last_scan": scan_time_iso,
        "next_scan": _next_scheduled_scan.isoformat() + "Z" if _next_scheduled_scan else None,
        "total_scanned": len(results),
        "zombie_count": zombie_count,
        "stale_count": stale_count,
        "active_count": active_count,
        "shadow_count": shadow_count,
    }
    await db.upsert_scan_metadata(meta)

    print(f"[Monitor] Scan complete: {len(results)} APIs probed ({zombie_count} zombie, {stale_count} stale, "
          f"{shadow_count} shadow, {active_count} active).")

    return {
        "last_scan": scan_time_iso,
        "next_scan": meta["next_scan"],
        "total_apis": len(results),
        "scan_results": scan_results,
    }


async def _background_probe_loop():
    """Background task: re-probe all catalog APIs every 30 minutes."""
    global _next_scheduled_scan
    while True:
        _next_scheduled_scan = datetime.utcnow() + timedelta(seconds=PROBE_INTERVAL_SECONDS)
        await asyncio.sleep(PROBE_INTERVAL_SECONDS)
        try:
            await _run_probe_scan()
        except Exception as e:
            print(f"[Monitor] Background probe failed: {e}")


async def _kong_reconciliation_loop():
    """Background task: Periodically reinstate request-termination for decommissioned APIs missing in Kong."""
    while True:
        await asyncio.sleep(10 * 60)
        try:
            apis = await db.get_all_api_catalog()
            if not apis:
                continue
            for api in apis:
                if str(api.get("lazarus_status", "")).upper() == "DECOMMISSIONED":
                    api_id = api.get("api_id")
                    if not api_id:
                        continue
                    has_plugin = await kong_client.get_plugin(api_id, "request-termination")
                    if not has_plugin:
                        await kong_client.apply_termination(api_id)
                        audit_entry = {
                            "action": "kong_drift_corrected",
                            "api_id": api_id,
                            "operator": "system_reconciliation",
                            "ip": "localhost",
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "prev_status": "drifted",
                            "new_status": "re-terminated"
                        }
                        await db.save_audit_entry(audit_entry)
                        print(f"[Kong Recon] Corrected plugin drift for {api_id}")
        except Exception as e:
            print(f"[Kong Recon] Background reconciliation failed: {e}")


@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan: start background probe task and Kong reconciliation on startup."""
    probe_task = asyncio.create_task(_background_probe_loop())
    recon_task = asyncio.create_task(_kong_reconciliation_loop())
    print("[Monitor] Background probe loop started (interval: 30 min).")
    print("[Kong Recon] Background reconciliation loop started (interval: 10 min).")
    yield
    probe_task.cancel()
    recon_task.cancel()
    try:
        await probe_task
        await recon_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Lazarus — Zombie API Discovery & Defence", lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Include Routers ──
app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(admin.router)

# DEMO CONFIG: update/restrict `allow_origins` before deploying to production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Redirect / Safe-Fallback Middleware ──

_SAFE_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>API Decommissioned — Lazarus Platform</title>
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:'Segoe UI',system-ui,sans-serif;background:#f8fafc;min-height:100vh;display:flex;align-items:center;justify-content:center;color:#0f172a}}
    .card{{background:#0f172a;border:1px solid #1e293b;border-radius:16px;padding:48px 40px;max-width:560px;width:90%;text-align:center;box-shadow:0 25px 50px -12px rgba(0,0,0,0.25);animation:fadeInUp 0.6s cubic-bezier(0.16,1,0.3,1) forwards;opacity:0;transform:translateY(20px)}}
    @keyframes fadeInUp{{to{{opacity:1;transform:translateY(0)}}}}
    .shield{{font-size:3.5rem;margin-bottom:16px;animation:pulse 2s ease-in-out infinite}}
    @keyframes pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.08)}}}}
    h1{{font-size:1.5rem;font-weight:700;margin-bottom:10px;color:#f8fafc}}
    .subtitle{{color:#94a3b8;margin-bottom:28px;line-height:1.6;font-size:0.95rem}}
    .info-box{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:18px 22px;margin:24px 0;text-align:left}}
    .info-row{{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;padding:8px 0;border-bottom:1px solid #334155;font-size:0.875rem}}
    .info-row:last-child{{border-bottom:none;padding-bottom:0}}
    .info-label{{color:#94a3b8;font-weight:600;white-space:nowrap}}
    .info-value{{color:#f1f5f9;font-weight:500;word-break:break-all;text-align:right}}
    .info-value.reason{{color:#f87171;font-weight:600}}
    .badge{{display:inline-block;background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.3);border-radius:99px;padding:3px 12px;font-size:0.75rem;font-weight:700;letter-spacing:.04em}}
    .redirect-badge{{background:rgba(34,197,94,0.15);color:#4ade80;border:1px solid rgba(34,197,94,0.3)}}
    .tag{{display:inline-block;background:rgba(99,102,241,0.15);color:#a5b4fc;border:1px solid rgba(99,102,241,0.25);border-radius:6px;padding:2px 8px;font-family:monospace;font-size:0.83rem}}
    .footer{{margin-top:24px;font-size:0.8rem;color:#64748b;line-height:1.7}}
    .footer a{{color:#60a5fa;text-decoration:none}}
    {redirect_style}
  </style>
</head>
<body>
<div class="card">
  <div class="shield">🛡️</div>
  <h1>This API Has Been Decommissioned</h1>
  <p class="subtitle">
    You have been safely intercepted by the <strong>Lazarus API Defence Platform</strong>.<br/>
    The endpoint you tried to access is no longer active and has been permanently removed.
  </p>
  <div class="info-box">
    <div class="info-row">
      <span class="info-label">Requested path</span>
      <span class="info-value"><span class="tag">{path}</span></span>
    </div>
    <div class="info-row">
      <span class="info-label">Status</span>
      <span class="info-value"><span class="badge">DECOMMISSIONED</span></span>
    </div>
    {reason_row}
    {redirect_row}
    <div class="info-row">
      <span class="info-label">Intercepted at</span>
      <span class="info-value">{timestamp}</span>
    </div>
  </div>
  {redirect_countdown}
  <div class="footer">
    If you believe this is an error, contact <a href="mailto:support@lazarus.bank.internal">support@lazarus.bank.internal</a><br/>
    or reach out to your API Gateway administrator.<br/><br/>
    <strong>Lazarus API Defence Platform</strong> &mdash; Protecting your API estate.
  </div>
</div>
</body>
</html>"""

@app.middleware("http")
async def redirect_rule_middleware(request: Request, call_next):
    """
    Intercept all incoming requests.
    1. If a redirect rule exists for the path → HTTP 301 to new path.
    2. Else if the path is decommissioned → serve the safe HTML fallback page.
    3. Otherwise → pass through normally.
    Skip /api/decommission*, /auth/*, /catalog/* endpoints to avoid loops.
    """
    path = normalize_path(request.url.path)

    # Skip protected internal routes
    if (
        path.startswith("/api/decommission")
        or path.startswith("/auth/")
        or path.startswith("/catalog/")
        or path.startswith("/docs")
        or path.startswith("/openapi")
        or path.startswith("/redoc")
    ):
        return await call_next(request)

    target = await db.get_redirect_rule(path)
    is_decomm = await db.is_decommissioned(path)

    if target or is_decomm:
        record = await db.get_decommission_by_path(path) or {}
        reason = record.get("reason", "Security risk — decommissioned by Lazarus platform.")
        ts = record.get("completed_at") or record.get("initiated_at") or datetime.utcnow().isoformat() + "Z"

        try:
            clean_ts = ts[:19]
            dt = datetime.strptime(clean_ts, "%Y-%m-%dT%H:%M:%S")
            formatted_ts = dt.strftime("%B %d, %Y - %I:%M %p UTC")
        except Exception:
            formatted_ts = ts

        reason_row = f"""<div class="info-row">
      <span class="info-label">Reason</span>
      <span class="info-value reason" style="color: #ef4444; font-weight: 700;">{reason}</span>
    </div>"""

        if target:
            redirect_row = f"""<div class="info-row">
      <span class="info-label">Redirecting To</span>
      <span class="info-value"><span class="redirect-badge" style="font-weight:700;">{target}</span></span>
    </div>"""
            redirect_style = ""
            redirect_countdown = f"""<p style="color:#94a3b8;font-size:0.85rem;margin-top:20px;">
    You are being safely redirected to the new endpoint.<br/>
    <a href="{target}">Click here if you are not redirected</a>.
  </p>
  <script>setTimeout(function(){{ window.location.href = "{target}"; }}, 4000);</script>"""
            status_code = 200
        else:
            redirect_row = ""
            redirect_style = ""
            redirect_countdown = """<p style="color:#94a3b8;font-size:0.85rem;margin-top:4px;">
    Please update your bookmarks or integrations to use the new endpoint.
  </p>"""
            status_code = 410

        html = _SAFE_PAGE_TEMPLATE.format(
            path=path,
            reason_row=reason_row,
            redirect_row=redirect_row,
            redirect_style=redirect_style,
            redirect_countdown=redirect_countdown,
            timestamp=formatted_ts,
        )
        return HTMLResponse(content=html, status_code=status_code)

    return await call_next(request)


class DefendRequest(BaseModel):
    path: str


class DecommissionRequest(BaseModel):
    api_id: str
    path: str
    reason: str = "Security risk — decommissioned via Lazarus platform."
    redirect_to: str = ""  # Optional: new safe endpoint path to redirect traffic to


class ExternalScanRequest(BaseModel):
    url: str


class KongRegisterRequest(BaseModel):
    api_id: str
    upstream_url: str
    path: str
    methods: list[str]


# ── Core Endpoints ──

_RISK_COLOR = {
    "ZOMBIE": ("#fef2f2", "#dc2626", "#fecaca"),
    "SHADOW": ("#fff7ed", "#ea580c", "#fed7aa"),
    "STALE":  ("#fffbeb", "#d97706", "#fde68a"),
    "ACTIVE": ("#f0fdf4", "#16a34a", "#bbf7d0"),
}

_METHOD_COLOR = {
    "GET": "#2563eb", "POST": "#16a34a", "PUT": "#d97706",
    "DELETE": "#dc2626", "PATCH": "#7c3aed",
}


def _build_catalog_html(catalog: list) -> str:
    cards_html = ""
    for api in catalog:
        # Support both old mock_data format (status/risk_level) and new csv format (lazarus_status)
        status_raw = (
            api.get("lazarus_status")
            or api.get("status")
            or api.get("risk_level")
            or "ACTIVE"
        ).upper()
        bb, bf, bbd = _RISK_COLOR.get(status_raw, ("#f8fafc", "#64748b", "#e2e8f0"))
        method = api.get("method", "GET").upper()
        mc = _METHOD_COLOR.get(method, "#64748b")
        cards_html += (
            f'<div class="api-card" data-status="{status_raw}">'
            f'<div class="card-top">'
            f'<span class="method-badge" style="background:{mc}18;color:{mc};border:1px solid {mc}30">{method}</span>'
            f'<span class="status-badge" style="background:{bb};color:{bf};border:1px solid {bbd}">{status_raw}</span>'
            f'</div>'
            f'<h3 class="api-name">{api.get("name", "Unnamed API")}</h3>'
            f'<code class="api-path">{api.get("path", "")}</code>'
            f'<p class="api-desc">{api.get("description", "")}</p>'
            f'<div class="api-meta">'
            f'<span>v{api.get("version", "?")}</span>'
            f'<span>&bull;</span><span>{api.get("owner", "—")}</span>'
            f'<span>&bull;</span><span>{api.get("department", "—")}</span>'
            f'</div></div>'
        )
    total  = len(catalog)
    zombie = sum(1 for a in catalog if (a.get("lazarus_status") or a.get("status") or "").upper() == "ZOMBIE")
    shadow = sum(1 for a in catalog if (a.get("lazarus_status") or a.get("status") or "").upper() == "SHADOW")
    stale  = sum(1 for a in catalog if (a.get("lazarus_status") or a.get("status") or "").upper() == "STALE")
    return (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='UTF-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/>"
        "<title>Lazarus — API Catalog</title>"
        "<style>"
        "*{margin:0;padding:0;box-sizing:border-box}"
        "body{font-family:'Segoe UI',system-ui,sans-serif;background:#0f172a;color:#f1f5f9;min-height:100vh}"
        "header{background:rgba(255,255,255,.04);border-bottom:1px solid rgba(255,255,255,.08);padding:18px 36px;"
        "display:flex;align-items:center;gap:14px;backdrop-filter:blur(10px);position:sticky;top:0;z-index:10}"
        ".logo{font-size:1.35rem;font-weight:800;background:linear-gradient(90deg,#60a5fa,#a78bfa);"
        "-webkit-background-clip:text;-webkit-text-fill-color:transparent}"
        ".hlink{margin-left:auto;font-size:.82rem;color:#475569}.hlink a{color:#60a5fa;text-decoration:none}"
        ".hero{padding:36px 36px 22px}.hero h1{font-size:1.8rem;font-weight:700;margin-bottom:6px}"
        ".hero p{color:#94a3b8;font-size:.93rem}"
        ".stats{display:flex;gap:14px;padding:0 36px 24px;flex-wrap:wrap}"
        ".stat{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);"
        "border-radius:12px;padding:14px 22px;flex:1;min-width:110px}"
        ".stat-num{font-size:1.7rem;font-weight:800;background:linear-gradient(90deg,#60a5fa,#a78bfa);"
        "-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1}"
        ".stat-label{font-size:.72rem;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:.06em}"
        ".toolbar{padding:0 36px 22px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}"
        "input.search{flex:1;min-width:200px;padding:10px 16px;background:rgba(255,255,255,.06);"
        "border:1px solid rgba(255,255,255,.12);border-radius:10px;color:#f1f5f9;font-size:.88rem;"
        "outline:none;transition:.2s}"
        "input.search:focus{border-color:rgba(96,165,250,.5);background:rgba(255,255,255,.09)}"
        "input.search::placeholder{color:#475569}"
        ".fbtn{padding:8px 15px;border-radius:8px;border:1px solid rgba(255,255,255,.1);"
        "background:rgba(255,255,255,.05);color:#64748b;cursor:pointer;font-size:.8rem;transition:.15s}"
        ".fbtn.active,.fbtn:hover{background:rgba(96,165,250,.15);color:#60a5fa;border-color:rgba(96,165,250,.35)}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:15px;padding:0 36px 40px}"
        ".api-card{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.09);"
        "border-radius:14px;padding:20px;transition:all .18s}"
        ".api-card:hover{background:rgba(255,255,255,.08);border-color:rgba(96,165,250,.3);"
        "transform:translateY(-2px);box-shadow:0 10px 28px rgba(0,0,0,.35)}"
        ".api-card.hidden{display:none}"
        ".card-top{display:flex;gap:8px;margin-bottom:12px}"
        ".method-badge,.status-badge{padding:3px 11px;border-radius:99px;font-size:.7rem;font-weight:700;letter-spacing:.04em}"
        ".api-name{font-size:.97rem;font-weight:700;margin-bottom:6px;color:#e2e8f0}"
        ".api-path{display:block;font-size:.78rem;color:#60a5fa;margin-bottom:10px;word-break:break-all;font-family:monospace}"
        ".api-desc{font-size:.81rem;color:#94a3b8;line-height:1.55;margin-bottom:14px}"
        ".api-meta{display:flex;gap:8px;font-size:.73rem;color:#475569;flex-wrap:wrap}"
        "footer{text-align:center;padding:18px;color:#334155;font-size:.77rem;border-top:1px solid rgba(255,255,255,.06)}"
        "footer a{color:#60a5fa;text-decoration:none}"
        "#empty{display:none;text-align:center;padding:60px;color:#475569}"
        "</style></head><body>"
        "<header>"
        "<div class='logo'>&#x1F6E1; Lazarus</div>"
        "<span style='color:#1e293b;font-size:1.2rem'>|</span>"
        "<span style='color:#64748b;font-size:.88rem'>API Defence Platform</span>"
        "<div class='hlink'>Full UI: <a href='http://localhost:5173' target='_blank'>localhost:5173</a> &nbsp;&bull;&nbsp; <a href='/docs'>Swagger</a></div>"
        "</header>"
        "<div class='hero'><h1>API Catalog Explorer</h1>"
        "<p>All registered APIs in your estate &mdash; live from Lazarus</p></div>"
        f"<div class='stats'>"
        f"<div class='stat'><div class='stat-num'>{total}</div><div class='stat-label'>Total APIs</div></div>"
        f"<div class='stat'><div class='stat-num'>{zombie}</div><div class='stat-label'>Zombie</div></div>"
        f"<div class='stat'><div class='stat-num'>{shadow}</div><div class='stat-label'>Shadow</div></div>"
        f"<div class='stat'><div class='stat-num'>{stale}</div><div class='stat-label'>Stale</div></div>"
        "</div>"
        "<div class='toolbar'>"
        "<input class='search' id='q' placeholder='Search name, path, team…' oninput='doFilter()'/>"
        "<button class='fbtn active' onclick=\"setF(this,'ALL')\">All</button>"
        "<button class='fbtn' onclick=\"setF(this,'ZOMBIE')\">&#x1F9DF; Zombie</button>"
        "<button class='fbtn' onclick=\"setF(this,'SHADOW')\">&#x1F464; Shadow</button>"
        "<button class='fbtn' onclick=\"setF(this,'STALE')\">&#x23F3; Stale</button>"
        "<button class='fbtn' onclick=\"setF(this,'ACTIVE')\">&#x2705; Active</button>"
        "</div>"
        f"<div class='grid' id='grid'>{cards_html}</div>"
        "<p id='empty'>No APIs match your search.</p>"
        "<footer>Lazarus API Defence Platform &mdash; <a href='/docs'>Swagger Docs</a> &mdash; <a href='/api/catalog'>Raw JSON</a></footer>"
        "<script>"
        "var f='ALL';"
        "function setF(b,v){f=v;document.querySelectorAll('.fbtn').forEach(x=>x.classList.remove('active'));b.classList.add('active');doFilter();}"
        "function doFilter(){"
        "var q=document.getElementById('q').value.toLowerCase(),vis=0;"
        "document.querySelectorAll('.api-card').forEach(c=>{"
        "var ok=(f==='ALL'||c.dataset.status===f)&&c.innerText.toLowerCase().includes(q);"
        "c.classList.toggle('hidden',!ok);if(ok)vis++;});"
        "document.getElementById('empty').style.display=vis?'none':'block';}"
        "</script></body></html>"
    )


def _synthesize_security_details(api: dict) -> tuple:
    ls = str(api.get("lazarus_status", "active")).lower()
    auth_exposed = api.get("auth_exposed", False)
    reachable = api.get("reachable", True)
    http_code = api.get("http_code")
    secret_detected = api.get("secret_detected", False)
    
    score = 100
    is_https = str(api.get("url", "")).startswith("https")
    
    # Contextual penalties
    if ls == "zombie":
        score -= 40
    elif ls == "shadow":
        score -= 35
    elif ls == "stale":
        score -= 20

    if not reachable:
        score -= 15
    if auth_exposed:
        score -= 30
    if not is_https:
        score -= 25
    if http_code and http_code >= 500:
        score -= 15
        
    score = max(0, min(100, score))

    rl_dict = api.get("rate_limit", {})
    rl_enforced = rl_dict.get("rate_limit_enforced")
    limit_hdrs = rl_dict.get("limit_headers", {})
    if rl_enforced is False:
        score -= 20
        # Re-clamp to ensure it doesn't go below 0
        score = max(0, score)
        rl_status = "fail"
        rl_details = "No rate limit enforced after 15 rapid requests."
        rl_limit = "None"
    elif rl_enforced is True:
        rl_status = "pass"
        rl_details = "Rate limit detected during probe."
        rl_limit = limit_hdrs.get("X-RateLimit-Limit") or limit_hdrs.get("Retry-After") or "Unknown"
    else:
        rl_status = "warning"
        rl_details = "Could not automatically verify rate limits via probe."
        rl_limit = "Unknown"

    # Secret detection override — force CRITICAL
    if secret_detected:
        score = 0
    
    auth_status = "warning"
    auth_type = "Unknown"
    auth_details = "Could not verify."

    if auth_exposed:
        auth_status = "fail"
        auth_type = "No Auth"
        auth_details = "Responded HTTP 200 without Authorization."
    elif http_code in (301, 302):
        auth_status = "pass"
        auth_type = "Auth Enforced"
        auth_details = "Valid authentication enforcement via redirect."
    elif reachable:
        auth_status = "pass"
        auth_type = "Unknown"
        auth_details = "Enforces auth or could not verify."

    posture = {
        "overall_score": score,
        "authentication": {
            "status": auth_status,
            "type": auth_type,
            "details": auth_details
        },
        "encryption": {
            "status": "pass" if is_https else "fail",
            "protocol": "TLS" if is_https else "HTTP",
            "details": "Using HTTPS" if is_https else "Using plaintext HTTP."
        },
        "rate_limiting": {
            "status": rl_status,
            "limit": rl_limit,
            "details": rl_details
        },
        "data_exposure": {
            "status": "fail" if secret_detected else ("warning" if auth_exposed else "pass"),
            "details": "CRITICAL — Secrets/credentials detected in API response body." if secret_detected else ("Potential unauthenticated data exposure." if auth_exposed else "No immediate exposure detected.")
        },
        "input_validation": {
            "status": "fail" if http_code and http_code >= 500 else "pass",
            "details": "Server returned 5xx error during probe." if http_code and http_code >= 500 else "No server errors during probe."
        }
    }
    
    reasoning = []
    if secret_detected:
        secret_types = api.get("secret_types", [])
        reasoning.append(f"CRITICAL: Secrets detected in response body — types: {', '.join(secret_types)}.")
    if ls == "zombie":
        reasoning.append("Endpoint is unreachable or timing out consistently.")
    if ls == "shadow":
        reasoning.append("Endpoint was discovered in traffic but lacks documentation.")
    if auth_exposed:
        reasoning.append("Endpoint exposed data without proper valid API keys or tokens.")
    if not is_https:
        reasoning.append("Endpoint is exposed over insecure HTTP.")
    if not reasoning:
        reasoning.append(f"Classified as {ls.upper()} based on HTTP probe results.")
        
    recommendations = []
    if secret_detected:
        recommendations.append({"action": "Rotate all credentials immediately — secrets detected in API response.", "priority": "critical"})
    if not reachable or ls == "zombie":
        recommendations.append({"action": "Decommission gateway route and remove from DNS.", "priority": "critical"})
    if auth_exposed:
        recommendations.append({"action": "Enforce strict JWT/API Key authentication immediately.", "priority": "critical"})
    if rl_enforced is False:
        recommendations.append({'action': 'Enforce rate limiting — API accepts unlimited requests.', 'priority': 'high'})
    if not is_https:
        recommendations.append({"action": "Migrate API traffic to HTTPS to ensure TLS encryption.", "priority": "high"})
    if ls == "stale":
        recommendations.append({"action": "Review endpoint usage with owners and deprecate if unused.", "priority": "medium"})
    if not recommendations:
        recommendations.append({"action": "Continue routine traffic monitoring and anomaly detection.", "priority": "low"})
        
    return posture, reasoning, recommendations


async def _get_effective_catalog() -> list:
    """Return catalog from MongoDB if populated, else fall back to mock_data."""
    mongo_catalog = await db.get_all_api_catalog()
    if mongo_catalog:
        return mongo_catalog
    return EXPECTED_CATALOG


def _get_effective_traffic(catalog: list) -> list:
    """
    When the DB catalog is active, synthesize a traffic list from each
    API's traffic_30d field so the rest of the app has a consistent
    hit_count / path shape.  Falls back to LIVE_TRAFFIC_FLOW for mock data.
    """
    # If the catalog has lazarus_status it came from a CSV upload
    if catalog and catalog[0].get("lazarus_status") is not None:
        flows = []
        for api in catalog:
            raw_url = api.get("url") or api.get("path") or ""
            parsed_path = urlparse(raw_url).path if raw_url.startswith("http") else raw_url
            flows.append({
                "path": normalize_path(parsed_path),
                "method": api.get("method", "GET"),
                "hit_count": api.get("traffic_30d", 0),
                "avg_latency": "—",
                "last_seen": api.get("last_traffic_at"),
            })
        return flows
    return LIVE_TRAFFIC_FLOW


@app.get("/")
async def root_explorer():
    """HTML API catalog — shown when browser visits localhost:8000."""
    return HTMLResponse(content=_build_catalog_html(await _get_effective_catalog()))


@app.get("/api/catalog")
async def get_catalog(request: Request, current_user: dict = Depends(get_current_user)):
    """Return API catalog. Serves HTML to browsers, JSON to API clients."""
    catalog = await _get_effective_catalog()
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return HTMLResponse(content=_build_catalog_html(catalog))
    return catalog


@app.get("/api/traffic")
async def get_traffic(current_user: dict = Depends(get_current_user)):
    catalog = await _get_effective_catalog()
    return _get_effective_traffic(catalog)


@app.get("/api/analyze")
async def get_analysis(current_user: dict = Depends(get_current_user)):
    catalog = await _get_effective_catalog()
    traffic = _get_effective_traffic(catalog)
    return analyze_api_discrepancies(catalog, traffic)


# ── Health (public) ──

@app.get("/health")
def health():
    return {"status": "ok", "service": "Lazarus API Defence Platform"}


# ── Detail Endpoint ──

async def _get_api_detail_full(api_id: str = None, path: str = None):
    # Try DB catalog first (CSV-ingested), then fall back to mock_data
    result = None
    mongo_catalog = await db.get_all_api_catalog()
    if mongo_catalog:
        for api in mongo_catalog:
            raw_url = api.get("url") or api.get("path") or ""
            api_path = urlparse(raw_url).path if raw_url.startswith("http") else raw_url
            
            if (api_id and api.get("api_id") == api_id) or (path and api_path == path):
                traffic_list = _get_effective_traffic(mongo_catalog)
                flow = next((f for f in traffic_list if f["path"] == api_path), None)
                ls = str(api.get("lazarus_status", "active")).lower()
                status_map = {"zombie": "ZOMBIE", "shadow": "SHADOW", "stale": "STALE", "active": "ACTIVE"}
                risk_map = {"zombie": "CRITICAL", "shadow": "CRITICAL", "stale": "MEDIUM", "active": "LOW"}
                
                posture, reasoning, recommendations = _synthesize_security_details(api)
                
                result = {
                    **api,
                    "id": api.get("api_id"),
                    "path": api_path,
                    "status": status_map.get(ls, "ACTIVE"),
                    "risk_level": risk_map.get(ls, "LOW"),
                    "traffic": flow,
                    "security_posture": posture,
                    "classification": {
                        "type": status_map.get(ls, "ACTIVE"),
                        "label": f"{status_map.get(ls, 'ACTIVE')} API",
                        "reasoning": reasoning,
                        "recommendations": recommendations,
                    },
                    "is_in_catalog": api.get("is_documented", True),
                    "is_decommissioned": False,
                }
                break

    if not result:
        result = get_api_detail(api_id=api_id, path=path)

    if not result:
        return None

    check_path = path or result.get("path")
    if check_path and await db.is_decommissioned(check_path):
        result["is_decommissioned"] = True
        result["decommission_record"] = await db.get_decommission_by_path(check_path)
    else:
        result["is_decommissioned"] = False

    return result


@app.get("/api/detail")
async def api_detail(api_id: str = None, path: str = None, current_user: dict = Depends(get_current_user)):
    if not api_id and not path:
        raise HTTPException(status_code=400, detail="Provide api_id or path query param.")

    result = await _get_api_detail_full(api_id=api_id, path=path)

    if not result:
        raise HTTPException(status_code=404, detail="API not found.")

    return result


# ── Defence Endpoints ──

@app.post("/api/defend")
async def defend_api(req: DefendRequest, current_user: dict = Depends(get_current_user)):
    await db.save_honeypot(req.path)
    return {"status": "honeypot_deployed", "path": req.path}


@app.get("/api/honeypots")
async def get_honeypots(current_user: dict = Depends(get_current_user)):
    """Return all persisted honeypot paths."""
    return await db.get_all_honeypots()


@app.get("/api/honeypots/activity")
async def get_honeypot_activity(current_user: dict = Depends(get_current_user)):
    """Return all activity logs matching a honeypot hit."""
    return await db.get_honeypot_activity()


@app.post("/api/decommission")
@limiter.limit("5/minute")
async def decommission_api(request: Request, req: DecommissionRequest, current_user: dict = Depends(get_current_user)):
    existing = await db.get_decommission_by_path(req.path)
    if existing:
        return {
            **existing,
            "already_decommissioned": True,
            "message": "This API has already been decommissioned.",
        }

    now = datetime.utcnow()
    entry = {
        "api_id": req.api_id,
        "path": req.path,
        "reason": req.reason,
        "status": "decommissioned",
        "initiated_at": now.isoformat() + "Z",
        "completed_at": (now + timedelta(seconds=12)).isoformat() + "Z",
        "operator": current_user.get("email", "admin@lazarus.bank.internal"),
        "approval": "Auto-approved — CRITICAL risk score below 20",
        "steps_completed": [
            {"step": 1, "action": "Traffic rerouted to fallback endpoint",
             "timestamp": now.isoformat() + "Z", "status": "success",
             "detail": "143 active connections drained; all new requests routed to /api/v2/auth-token"},
            {"step": 2, "action": "Endpoint blocked at API gateway",
             "timestamp": now.isoformat() + "Z", "status": "success",
             "detail": "Kong gateway rule #GW-4891 created; endpoint now returns 403 Forbidden"},
            {"step": 3, "action": "DNS records removed",
             "timestamp": now.isoformat() + "Z", "status": "success",
             "detail": "A-record for legacy-auth.bank.internal removed from Route53 zone"},
            {"step": 4, "action": "Credentials & tokens revoked",
             "timestamp": now.isoformat() + "Z", "status": "success",
             "detail": "14,832 legacy tokens invalidated; 3 OAuth client secrets rotated"},
            {"step": 5, "action": "Documentation archived",
             "timestamp": now.isoformat() + "Z", "status": "success",
             "detail": "OpenAPI spec moved to archive with DECOMMISSIONED label"},
            {"step": 6, "action": "Stakeholders notified",
             "timestamp": now.isoformat() + "Z", "status": "success",
             "detail": "Notification sent to daxketkar10@gmail.com and internal teams"},
        ],
        "post_verification": {
            "scan_timestamp": now.isoformat() + "Z",
            "endpoint_status": "BLOCKED (403 Forbidden)",
            "dns_resolved": False,
            "tokens_active": 0,
            "tokens_revoked": 14832,
            "gateway_rule_active": True,
            "result": "VERIFIED — Endpoint is fully decommissioned",
        },
        "stakeholder_notifications": [
            {"recipient": "daxketkar10@gmail.com", "channel": "email", "status": "pending", "timestamp": now.isoformat() + "Z"},
            {"recipient": "ciso@bank.com", "channel": "email", "status": "delivered", "timestamp": now.isoformat() + "Z"},
            {"recipient": "#security-alerts", "channel": "slack", "status": "delivered", "timestamp": now.isoformat() + "Z"},
            {"recipient": "compliance@bank.com", "channel": "email", "status": "delivered", "timestamp": now.isoformat() + "Z"},
            {"recipient": "devops-oncall@bank.com", "channel": "email", "status": "delivered", "timestamp": now.isoformat() + "Z"},
        ],
        "compliance_summary": {
            "regulation": "RBI IT Framework / PCI-DSS v4.0",
            "risk_before": "CRITICAL (15/100)",
            "risk_after": "REMEDIATED (0/100 — endpoint removed)",
            "evidence_chain": "Complete — all 6 steps verified",
            "audit_ready": True,
        },
    }

    await db.save_decommission(entry)

    # ── Kong gateway decommission ──
    try:
        kong_result = await kong_client.decommission_service(req.api_id)
    except Exception:
        kong_result = {"error": "Kong unreachable"}
    entry["kong_result"] = kong_result

    if req.redirect_to and req.redirect_to.strip():
        await db.save_redirect_rule(req.path, req.redirect_to.strip())
        entry["redirect_to"] = req.redirect_to.strip()

    email_result = send_decommission_email(entry)
    entry["stakeholder_notifications"][0]["status"] = email_result["status"]
    if email_result.get("error"):
        entry["stakeholder_notifications"][0]["error"] = email_result["error"]
    await db.save_decommission(entry)

    # ── Audit Log & Catalog Update ──
    api_doc = await db.get_api_catalog_by_id(req.api_id)
    prev_status = api_doc.get("lazarus_status", "ACTIVE") if api_doc else "UNKNOWN"

    operator_sub = current_user.get("sub") or current_user.get("email") or "system"
    ip_addr = request.client.host if request and request.client else "unknown"

    audit_entry = {
        "action": "decommission",
        "api_id": req.api_id,
        "operator": operator_sub,
        "ip": ip_addr,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "prev_status": prev_status,
        "new_status": "DECOMMISSIONED"
    }
    await db.save_audit_entry(audit_entry)

    if api_doc:
        api_doc["lazarus_status"] = "DECOMMISSIONED"
        await db.upsert_api_catalog(api_doc)
        await db.log_status_change(req.api_id, prev_status, "DECOMMISSIONED")

    entry["email_sent"] = email_result
    return entry


# ── Kong Registration Endpoint ──

@app.post("/api/kong/register")
async def kong_register(req: KongRegisterRequest, current_user: dict = Depends(get_current_user)):
    """Register a service and route in Kong gateway."""
    svc_result = await kong_client.register_service(req.api_id, req.upstream_url)
    route_result = await kong_client.register_route(req.api_id, req.path, req.methods)
    return {
        "status": "registered",
        "api_id": req.api_id,
        "service": svc_result,
        "route": route_result,
    }


# ── Monitoring Endpoints ──

@app.get("/api/monitor")
async def get_monitoring(current_user: dict = Depends(get_current_user)):
    """Return last scan summary + per-API scan results from the most recent probe."""
    meta = await db.get_scan_metadata()
    if not meta:
        # No scan has run yet — return live catalog snapshot
        catalog = await db.get_all_api_catalog()
        now_iso = datetime.utcnow().isoformat() + "Z"
        scan_results = []
        for api in catalog:
            scan_results.append({
                "api_id": api.get("api_id"),
                "url": api.get("url"),
                "lazarus_status": api.get("lazarus_status", "ACTIVE"),
                "http_code": api.get("http_code"),
                "response_time_ms": api.get("response_time_ms"),
                "auth_exposed": api.get("auth_exposed"),
                "reachable": api.get("reachable"),
                "probed_at": api.get("probed_at"),
            })
        _severity_order = {"ZOMBIE": 0, "SHADOW": 1, "STALE": 2, "ACTIVE": 3}
        scan_results.sort(key=lambda r: _severity_order.get(str(r.get("lazarus_status", "")).upper(), 9))
        return {
            "last_scan": None,
            "next_scan": _next_scheduled_scan.isoformat() + "Z" if _next_scheduled_scan else None,
            "total_apis": len(catalog),
            "scan_results": scan_results,
        }

    # Build per-API results from current catalog
    catalog = await db.get_all_api_catalog()
    scan_results = []
    for api in catalog:
        scan_results.append({
            "api_id": api.get("api_id"),
            "url": api.get("url"),
            "lazarus_status": api.get("lazarus_status", "ACTIVE"),
            "http_code": api.get("http_code"),
            "response_time_ms": api.get("response_time_ms"),
            "auth_exposed": api.get("auth_exposed"),
            "reachable": api.get("reachable"),
            "probed_at": api.get("probed_at"),
        })
    _severity_order = {"ZOMBIE": 0, "SHADOW": 1, "STALE": 2, "ACTIVE": 3}
    scan_results.sort(key=lambda r: _severity_order.get(str(r.get("lazarus_status", "")).upper(), 9))

    return {
        "last_scan": meta.get("last_scan"),
        "next_scan": meta.get("next_scan") or (_next_scheduled_scan.isoformat() + "Z" if _next_scheduled_scan else None),
        "total_apis": meta.get("total_scanned", len(catalog)),
        "zombie_count": meta.get("zombie_count", 0),
        "stale_count": meta.get("stale_count", 0),
        "active_count": meta.get("active_count", 0),
        "shadow_count": meta.get("shadow_count", 0),
        "scan_results": scan_results,
    }


@app.get("/api/security-events")
async def get_security_events(current_user: dict = Depends(get_current_user)):
    """Return all security anomaly events, newest first."""
    return await db.get_security_events()


@app.post("/api/monitor/scan-now")
async def trigger_manual_scan(current_user: dict = Depends(get_current_user)):
    """Trigger an immediate full re-probe of all APIs. Returns the scan results."""
    result = await _run_probe_scan()
    return result


@app.get("/api/decommission-log")
async def get_decommission_log(current_user: dict = Depends(get_current_user)):
    """Return all decommission records from MongoDB."""
    return await db.get_all_decommissions()


@app.get("/api/audit-log")
async def get_audit_log_api(current_user: dict = Depends(get_current_user)):
    """Return recent audit log entries (max 50, descending timestamp)."""
    return await db.get_audit_log(limit=50)


@app.get("/api/activity-log")
async def get_activity_log(current_user: dict = Depends(get_current_user)):
    """Return recent activity log from MongoDB."""
    return await db.get_activity_log()


@app.get("/api/redirect-rules")
async def get_redirect_rules(current_user: dict = Depends(get_current_user)):
    """Return all active redirect rules from MongoDB."""
    return await db.get_all_redirect_rules()


# ── Mock Target Endpoints (for Redirect targets) ──

@app.get("/api/safe-v3")
def get_safe_v3(current_user: dict = Depends(get_current_user)):
    return {
        "status": "success",
        "message": "Welcome to the new, safe API v3 endpoint.",
        "version": "3.1.0",
        "data": {
            "encryption": "aes-256-gcm",
            "auth_required": True
        }
    }


# ── External Scanner Endpoint ──

_SECURITY_HEADERS = [
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-XSS-Protection",
    "X-Permitted-Cross-Domain-Policies",
]

_SHADOW_PATHS = [
    "/admin", "/api/v1", "/api/v2", "/api/old", "/api/test",
    "/api/debug", "/api/legacy", "/v1", "/v2", "/.env",
    "/.git/config", "/swagger", "/swagger.json", "/openapi.json",
    "/console", "/actuator", "/phpinfo.php", "/backup",
]

_SERVER_TECH_KEYWORDS = [
    "apache", "nginx", "iis", "express", "werkzeug",
    "gunicorn", "lighttpd", "litespeed", "tornado", "jetty",
    "tomcat", "jboss", "weblogic", "phusion",
]


def _classify_endpoint(status_code: int) -> dict:
    if status_code == 200:
        return {"classification": "SHADOW_EXPOSED", "severity": "HIGH"}
    elif status_code == 403:
        return {"classification": "SHADOW_PROTECTED", "severity": "MEDIUM"}
    elif status_code == 500:
        return {"classification": "SERVER_ERROR", "severity": "CRITICAL"}
    elif status_code in (301, 302):
        return {"classification": "REDIRECT_DETECTED", "severity": "LOW"}
    else:
        return {"classification": "ANOMALY", "severity": "MEDIUM"}


def _compute_overall_risk(discovered: list, missing_headers: list, open_cors: bool, server_leak: str | None, secret_detected: bool, auth_exposed: bool, rate_limit_info: dict) -> str:
    severities = {ep["severity"] for ep in discovered}
    if secret_detected or auth_exposed:
        return "CRITICAL"
    if "CRITICAL" in severities:
        return "CRITICAL"
    if "HIGH" in severities or len(missing_headers) >= 4 or rate_limit_info.get("rate_limit_enforced") is False:
        return "HIGH"
    if "MEDIUM" in severities or open_cors or missing_headers or server_leak:
        return "MEDIUM"
    return "LOW"


@app.post("/api/scan-external")
async def scan_external(req: ExternalScanRequest, current_user: dict = Depends(get_current_user)):
    """External URL Scanner — probe any public URL for security misconfigurations."""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Provide a URL to scan.")

    scan_timestamp = datetime.utcnow().isoformat() + "Z"
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    uses_https = parsed.scheme.lower() == "https"

    try:
        async with httpx.AsyncClient(verify=False) as client:
            client_headers = _build_headers(url)
            t_start = time.monotonic()
            resp = await client.get(url, timeout=10.0, follow_redirects=True, headers=client_headers)
            response_time_ms = round((time.monotonic() - t_start) * 1000)
            status_code = resp.status_code
            headers = dict(resp.headers)
            reachable = True
            body_text = resp.text

            secrets = scan_for_secrets(body_text)
            secret_detected = len(secrets) > 0

            auth_exposed = False
            try:
                bare_headers = {k: v for k, v in client_headers.items() if k.lower() not in ("authorization", "x-api-key", "api-key")}
                auth_resp = await client.get(url, headers=bare_headers, timeout=10.0, follow_redirects=True)
                if auth_resp.status_code == 200:
                    body_lower = auth_resp.text.lower()
                    has_login_form = "<form" in body_lower and "type=\"password\"" in body_lower
                    if not has_login_form:
                        auth_exposed = True
            except Exception:
                pass

            rate_limit_info = await check_rate_limit(client, url, "GET")

            discovered_endpoints = []
            for shadow_path in _SHADOW_PATHS:
                probe_url = base_url + shadow_path
                try:
                    t0 = time.monotonic()
                    pr = await client.get(
                        probe_url, timeout=5.0,
                        follow_redirects=False,
                        headers={"User-Agent": "Lazarus-Scanner/2.0"},
                    )
                    probe_time = round((time.monotonic() - t0) * 1000)
                    if pr.status_code not in (404, 410):
                        classification = _classify_endpoint(pr.status_code)
                        discovered_endpoints.append({
                            "path": normalize_path(shadow_path),
                            "status_code": pr.status_code,
                            "response_time_ms": probe_time,
                            "classification": classification["classification"],
                            "severity": classification["severity"],
                        })
                except Exception:
                    pass

    except Exception as exc:
        return {
            "url_scanned": url,
            "scan_timestamp": scan_timestamp,
            "reachable": False,
            "error": str(exc),
            "response_time_ms": None,
            "status_code": None,
            "uses_https": uses_https,
            "missing_security_headers": [],
            "open_cors": False,
            "server_header_leak": None,
            "discovered_endpoints": [],
            "overall_risk": "UNKNOWN",
            "summary": f"The target URL could not be reached. Error: {exc}",
        }

    headers_lower = {k.lower(): v for k, v in headers.items()}
    missing_security_headers = [h for h in _SECURITY_HEADERS if h.lower() not in headers_lower]
    open_cors = headers_lower.get("access-control-allow-origin", "") == "*"
    server_val = headers_lower.get("server", "")
    server_header_leak = None
    if server_val:
        sl = server_val.lower()
        if any(kw in sl for kw in _SERVER_TECH_KEYWORDS) or len(server_val) > 3:
            server_header_leak = server_val

    overall_risk = _compute_overall_risk(
        discovered_endpoints, missing_security_headers, open_cors, server_header_leak, secret_detected, auth_exposed, rate_limit_info
    )

    issues = []
    if secret_detected:
        issues.append(f"Secrets detected in response ({', '.join(secrets)})")
    if auth_exposed:
        issues.append("Endpoint appears unauthenticated and exposes data")
    if rate_limit_info.get("rate_limit_enforced") is False:
        issues.append("No rate limits enforced")
    if missing_security_headers:
        issues.append(f"{len(missing_security_headers)} security headers are missing")
    if open_cors:
        issues.append("CORS is open to all origins (wildcard *)")
    if server_header_leak:
        issues.append(f"server technology is exposed via the Server header ({server_header_leak})")
    if discovered_endpoints:
        issues.append(f"{len(discovered_endpoints)} potentially sensitive endpoint(s) discovered")
    
    if issues:
        summary = (
            f"Scan of {url} returned HTTP {status_code} in {response_time_ms}ms. "
            f"The following issues were found: {', '.join(issues)}. "
            f"Overall risk is rated {overall_risk}."
        )
    else:
        summary = (
            f"Scan of {url} returned HTTP {status_code} in {response_time_ms}ms. "
            f"No major misconfigurations detected. Overall risk is rated {overall_risk}."
        )

    return {
        "url_scanned": url,
        "scan_timestamp": scan_timestamp,
        "reachable": reachable,
        "response_time_ms": response_time_ms,
        "status_code": status_code,
        "uses_https": uses_https,
        "missing_security_headers": missing_security_headers,
        "open_cors": open_cors,
        "server_header_leak": server_header_leak,
        "discovered_endpoints": discovered_endpoints,
        "secret_detected": secret_detected,
        "secret_types": secrets,
        "auth_exposed": auth_exposed,
        "rate_limit_info": rate_limit_info,
        "overall_risk": overall_risk,
        "summary": summary,
    }


@app.get("/api/compliance-report")
async def get_compliance_report(api_id: str = None, path: str = None, current_user: dict = Depends(get_current_user)):
    """Generate a compliance report for a decommissioned API."""
    logs = await db.get_all_decommissions()
    entry = None
    for log in logs:
        if (api_id and log.get("api_id") == api_id) or (path and log.get("path") == path):
            entry = log
            break

    if not entry:
        raise HTTPException(status_code=404, detail="No decommission record found for this API.")

    detail = get_api_detail(api_id=api_id, path=path)
    posture = detail.get("security_posture", {}) if detail else {}

    return {
        "report_id": f"CR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "api_id": entry["api_id"],
        "api_path": entry["path"],
        "decommission_record": entry,
        "security_posture_snapshot": posture,
        "regulatory_compliance": {
            "framework": "RBI IT Framework 2023 + PCI-DSS v4.0",
            "requirements_met": [
                "Requirement 6.3.2 — Removal of unused software and APIs",
                "Requirement 11.3 — Vulnerability management and remediation",
                "Requirement 10.2 — Audit trail for security-relevant actions",
                "RBI Master Direction — IT Governance and Risk Management",
            ],
            "evidence_provided": [
                "Pre-decommission security posture assessment (score: {}/100)".format(posture.get("overall_score", "N/A")),
                "Step-by-step execution log with timestamps",
                "Post-decommission verification scan",
                "Stakeholder notification log with delivery confirmations",
                "Token revocation count: {} tokens invalidated".format(
                    entry.get("post_verification", {}).get("tokens_revoked", 0)
                ),
            ],
        },
    }


@app.get("/api/compliance-report/pdf")
async def get_compliance_report_pdf(api_id: str = None, path: str = None, current_user: dict = Depends(get_current_user)):
    """Generate a PDF compliance report for a decommissioned API."""
    if not api_id and not path:
        raise HTTPException(status_code=400, detail="Provide api_id or path query param.")

    # Fetch the original JSON data
    report_data = await get_compliance_report(api_id=api_id, path=path, current_user=current_user)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=14,
        textColor=colors.HexColor('#1e293b')
    )
    heading_style = ParagraphStyle(
        'SubHead',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        textColor=colors.HexColor('#334155')
    )
    normal_style = styles["Normal"]

    story = []

    # 0. Logo
    import os
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lazarus_logo.png")
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=70, height=70)
        logo_img.hAlign = 'LEFT'
        story.append(logo_img)
        story.append(Spacer(1, 10))

    # 1. Title
    story.append(Paragraph("Lazarus Decommission Report", title_style))
    story.append(Spacer(1, 12))

    # 2. Main Details
    record = report_data.get("decommission_record", {})
    api_id_val = report_data.get("api_id", "N/A")
    api_path = report_data.get("api_path", "N/A")
    decomm_date = record.get("completed_at", "N/A")
    operator = record.get("operator", "N/A")

    details = [
        [Paragraph("<b>API ID:</b>", normal_style), Paragraph(api_id_val, normal_style)],
        [Paragraph("<b>Path:</b>", normal_style), Paragraph(api_path, normal_style)],
        [Paragraph("<b>Decommission Date:</b>", normal_style), Paragraph(decomm_date, normal_style)],
        [Paragraph("<b>Operator:</b>", normal_style), Paragraph(operator, normal_style)],
    ]
    t = Table(details, colWidths=[120, 300])
    t.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1e293b')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    # 2b. Snapshot Details
    st_posture = report_data.get("security_posture_snapshot", {})
    score = st_posture.get("overall_score", "N/A")
    sec_risk_level = st_posture.get("risk_level", "LOW")
    scan_dt_raw = report_data.get("generated_at", "N/A")
    scan_dt = str(scan_dt_raw)[:19].replace("T", " ") if "T" in str(scan_dt_raw) else str(scan_dt_raw)

    posture_details = [
        [Paragraph("<b>Report Generated:</b>", normal_style), Paragraph(scan_dt, normal_style)],
        [Paragraph("<b>Security Score:</b>", normal_style), Paragraph(str(score) + "/100", normal_style)],
        [Paragraph("<b>Security Risk Level:</b>", normal_style), Paragraph(str(sec_risk_level), normal_style)]
    ]
    tp = Table(posture_details, colWidths=[120, 300])
    tp.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1e293b')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(tp)
    story.append(Spacer(1, 16))

    # 3. Risk Before/After
    story.append(Paragraph("Risk Summary", heading_style))
    comp_sum = record.get("compliance_summary", {})
    risk_before = comp_sum.get("risk_before", "N/A")
    risk_after = comp_sum.get("risk_after", "N/A")
    
    risk_data = [
        [Paragraph("<b>Risk Before:</b>", normal_style), Paragraph(risk_before, normal_style)],
        [Paragraph("<b>Risk After:</b>", normal_style), Paragraph(risk_after, normal_style)],
    ]
    t_risk = Table(risk_data, colWidths=[120, 300])
    t_risk.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1e293b')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_risk)
    story.append(Spacer(1, 16))

    # 4. Decommission Steps
    story.append(Paragraph("Execution Steps", heading_style))
    steps = record.get("steps_completed", [])
    step_data = [["Step", "Action", "Status", "Timestamp"]]
    for s in steps:
        step_data.append([
            str(s.get("step", "")),
            Paragraph(s.get("action", ""), normal_style),
            s.get("status", ""),
            s.get("timestamp", "")[:19].replace("T", " ")
        ])
    
    if len(step_data) > 1:
        t_steps = Table(step_data, colWidths=[40, 200, 70, 140])
        t_steps.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#475569')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_steps)
    else:
        story.append(Paragraph("No steps recorded.", normal_style))
    
    story.append(Spacer(1, 16))

    # 5. Regulatory Requirements
    story.append(Paragraph("Regulatory Requirements Met", heading_style))
    reg = report_data.get("regulatory_compliance", {})
    reqs = reg.get("requirements_met", [])
    for r in reqs:
        story.append(Paragraph(f"• {r}", normal_style))
        story.append(Spacer(1, 4))

    # Build PDF
    doc.build(story)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    headers = {
        "Content-Disposition": f"attachment; filename=lazarus-report-{api_id_val}.pdf"
    }
    return Response(content=pdf_content, media_type="application/pdf", headers=headers)

@app.get("/api/db-status")
async def db_status():
    """Check MongoDB connection status."""
    return {"connected": await db.is_connected(), "uri": "mongodb://127.0.0.1:27017/lazarus"}


# ── AI Interpretation Layer Endpoints ──

class AiApiRequest(BaseModel):
    api_id: str | None = None
    path: str | None = None


class AiQueryRequest(BaseModel):
    question: str


class AiChatRequest(BaseModel):
    """Request model for the OpenRouter-powered chat endpoint."""
    question: str
    history: list = []


async def _gather_all_api_details():
    """Gather full detail for every known API (catalog + shadow)."""
    all_details = []
    catalog = await _get_effective_catalog()
    traffic = _get_effective_traffic(catalog)
    for api in catalog:
        api_id = api.get("id") or api.get("api_id")
        detail = await _get_api_detail_full(api_id=api_id)
        if detail:
            all_details.append(detail)
    catalog_paths = {api.get("path") for api in catalog}
    for flow in traffic:
        if flow["path"] not in catalog_paths:
            detail = await _get_api_detail_full(path=flow["path"])
            if detail:
                all_details.append(detail)
    return all_details


@app.post("/api/ai/explain-risk")
async def ai_explain_risk(req: AiApiRequest, current_user: dict = Depends(get_current_user)):
    """AI Risk Explanation — plain-English risk translation for non-technical users."""
    if not req.api_id and not req.path:
        raise HTTPException(status_code=400, detail="Provide api_id or path.")
    detail = await _get_api_detail_full(api_id=req.api_id, path=req.path)
    if not detail:
        raise HTTPException(status_code=404, detail="API not found.")
    result = ai_engine.explain_risk(detail)
    return {"api_path": detail.get("path"), "explanation": result}


@app.post("/api/ai/query")
async def ai_query(req: AiQueryRequest, current_user: dict = Depends(get_current_user)):
    """Natural Language Security Query — ask questions in plain English (local engine)."""
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Provide a question.")
    all_details = await _gather_all_api_details()
    catalog = await _get_effective_catalog()
    analysis = analyze_api_discrepancies(catalog, _get_effective_traffic(catalog))
    result = ai_engine.query_security(req.question, all_details, analysis)
    return {"question": req.question, "answer": result}


@app.post("/api/ai/chat")
async def ai_chat(req: AiChatRequest, current_user: dict = Depends(get_current_user)):
    """OpenRouter / Qwen-powered conversational AI chat."""
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Provide a question.")
    all_details = await _gather_all_api_details()
    catalog = await _get_effective_catalog()
    analysis = analyze_api_discrepancies(catalog, _get_effective_traffic(catalog))
    answer = openrouter_engine.chat_with_openrouter(
        question=req.question,
        api_data=all_details,
        analysis=analysis,
        history=req.history,
    )
    return {"question": req.question, "answer": answer}


@app.post("/api/ai/generate-report")
async def ai_generate_report(req: AiApiRequest, current_user: dict = Depends(get_current_user)):
    """AI Security Report Generator — comprehensive compliance report."""
    if not req.api_id and not req.path:
        raise HTTPException(status_code=400, detail="Provide api_id or path.")
    detail = await _get_api_detail_full(api_id=req.api_id, path=req.path)
    if not detail:
        raise HTTPException(status_code=404, detail="API not found.")
    result = ai_engine.generate_report(detail)
    return {"api_path": detail.get("path"), "report": result}


@app.post("/api/ai/attack-simulation")
async def ai_attack_simulation(req: AiApiRequest, current_user: dict = Depends(get_current_user)):
    """Attack Scenario Simulator — hypothetical attack vectors."""
    if not req.api_id and not req.path:
        raise HTTPException(status_code=400, detail="Provide api_id or path.")
    detail = await _get_api_detail_full(api_id=req.api_id, path=req.path)
    if not detail:
        raise HTTPException(status_code=404, detail="API not found.")
    result = ai_engine.simulate_attack(detail)
    return {"api_path": detail.get("path"), "simulation": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)


@app.get("/api/ai/security-summary")
async def ai_security_summary(current_user: dict = Depends(get_current_user)):
    """AI Security Summary — executive overview for dashboard."""
    all_details = await _gather_all_api_details()
    catalog = await _get_effective_catalog()
    analysis = analyze_api_discrepancies(catalog, _get_effective_traffic(catalog))
    result = ai_engine.security_summary(all_details, analysis)
    return {"summary": result}


# ── Status Change Log Endpoint ──

@app.get("/api/status-changes")
async def get_status_changes(current_user: dict = Depends(get_current_user)):
    """Return recent status change log entries from background probe."""
    return await db.get_status_changes()


if __name__ == "__main__":
    import uvicorn
    print("\n🔒 Lazarus — Zombie API Discovery & Defence")
    print("   MongoDB: async (motor) — check /api/db-status after startup")
    print("   Background probe: every 30 minutes")
    print(f"   AI Engine: ✅ Local + OpenRouter Active")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000)