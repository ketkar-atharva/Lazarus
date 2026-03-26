from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from datetime import datetime
from mock_data import (
    EXPECTED_CATALOG,
    LIVE_TRAFFIC_FLOW,
    MONITORING_DATA,
    analyze_api_discrepancies,
    get_api_detail,
)
import ai_engine
import openrouter_engine
import database as db
from email_notifier import send_decommission_email
import requests as req_lib
import time
from urllib.parse import urlparse

app = FastAPI(title="Lazarus — Zombie API Discovery & Defence")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    Skip /api/decommission* endpoints to avoid infinite loops.
    """
    path = request.url.path

    if path.startswith("/api/decommission"):
        return await call_next(request)

    target = db.get_redirect_rule(path)
    is_decomm = db.is_decommissioned(path)

    if target or is_decomm:
        # It's decommissioned or redirected (which means it was decommissioned)
        record = db.get_decommission_by_path(path) or {}
        reason = record.get("reason", "Security risk — decommissioned by Lazarus platform.")
        ts = record.get("completed_at") or record.get("initiated_at") or datetime.utcnow().isoformat() + "Z"
        
        # Format the timestamp
        try:
            # Safely parse up to the seconds (e.g., 2026-03-26T05:30:31)
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
            status_code = 200 # OK to render the redirect intercept
        else:
            redirect_row = ""
            redirect_style = ""
            redirect_countdown = """<p style="color:#94a3b8;font-size:0.85rem;margin-top:4px;">
    Please update your bookmarks or integrations to use the new endpoint.
  </p>"""
            status_code = 410 # Gone

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
        status = (api.get("status") or api.get("risk_level") or "ACTIVE").upper()
        bb, bf, bbd = _RISK_COLOR.get(status, ("#f8fafc", "#64748b", "#e2e8f0"))
        method = api.get("method", "GET").upper()
        mc = _METHOD_COLOR.get(method, "#64748b")
        cards_html += (
            f'<div class="api-card" data-status="{status}">'
            f'<div class="card-top">'
            f'<span class="method-badge" style="background:{mc}18;color:{mc};border:1px solid {mc}30">{method}</span>'
            f'<span class="status-badge" style="background:{bb};color:{bf};border:1px solid {bbd}">{status}</span>'
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
    zombie = sum(1 for a in catalog if (a.get("status") or "").upper() == "ZOMBIE")
    shadow = sum(1 for a in catalog if (a.get("status") or "").upper() == "SHADOW")
    stale  = sum(1 for a in catalog if (a.get("status") or "").upper() == "STALE")
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


@app.get("/")
def root_explorer():
    """HTML API catalog — shown when browser visits localhost:8000."""
    return HTMLResponse(content=_build_catalog_html(EXPECTED_CATALOG))


@app.get("/api/catalog")
def get_catalog(request: Request):
    """Return API catalog. Serves HTML to browsers, JSON to API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return HTMLResponse(content=_build_catalog_html(EXPECTED_CATALOG))
    return EXPECTED_CATALOG


@app.get("/api/traffic")
def get_traffic():
    return LIVE_TRAFFIC_FLOW


@app.get("/api/analyze")
def get_analysis():
    return analyze_api_discrepancies(EXPECTED_CATALOG, LIVE_TRAFFIC_FLOW)


# ── Detail Endpoint ──

@app.get("/api/detail")
def api_detail(api_id: str = None, path: str = None):
    if not api_id and not path:
        raise HTTPException(status_code=400, detail="Provide api_id or path query param.")
    result = get_api_detail(api_id=api_id, path=path)
    if not result:
        raise HTTPException(status_code=404, detail="API not found.")

    # Enrich with decommission status from DB
    check_path = path or result.get("path")
    if check_path and db.is_decommissioned(check_path):
        result["is_decommissioned"] = True
        result["decommission_record"] = db.get_decommission_by_path(check_path)
    else:
        result["is_decommissioned"] = False

    return result


# ── Defence Endpoints ──

@app.post("/api/defend")
def defend_api(req: DefendRequest):
    db.save_honeypot(req.path)
    return {"status": "honeypot_deployed", "path": req.path}


@app.get("/api/honeypots")
def get_honeypots():
    """Return all persisted honeypot paths."""
    return db.get_all_honeypots()


@app.post("/api/decommission")
def decommission_api(req: DecommissionRequest):
    # Check if already decommissioned
    existing = db.get_decommission_by_path(req.path)
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
        "completed_at": (now.replace(second=now.second + 12)).isoformat() + "Z",
        "operator": "admin@lazarus.bank.internal",
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

    # Save to MongoDB
    db.save_decommission(entry)

    # Save redirect rule if a new safe path was provided
    if req.redirect_to and req.redirect_to.strip():
        db.save_redirect_rule(req.path, req.redirect_to.strip())
        entry["redirect_to"] = req.redirect_to.strip()

    # Send email notification
    email_result = send_decommission_email(entry)
    # Update the notification status for daxketkar10@gmail.com
    entry["stakeholder_notifications"][0]["status"] = email_result["status"]
    if email_result.get("error"):
        entry["stakeholder_notifications"][0]["error"] = email_result["error"]
    # Re-save with updated email status
    db.save_decommission(entry)

    entry["email_sent"] = email_result
    return entry


# ── Monitoring Endpoint ──

@app.get("/api/monitor")
def get_monitoring():
    return MONITORING_DATA


@app.get("/api/decommission-log")
def get_decommission_log():
    """Return all decommission records from MongoDB."""
    return db.get_all_decommissions()


@app.get("/api/activity-log")
def get_activity_log():
    """Return recent activity log from MongoDB."""
    return db.get_activity_log()


@app.get("/api/redirect-rules")
def get_redirect_rules():
    """Return all active redirect rules from MongoDB."""
    return db.get_all_redirect_rules()

# ── Mock Target Endpoints (for Redirect targets) ──

@app.get("/api/safe-v3")
def get_safe_v3():
    return {
        "status": "success",
        "message": "Welcome to the new, safe API v3 endpoint.",
        "version": "3.1.0",
        "data": {
            "encryption": "aes-256-gcm",
            "auth_required": True
        }
    }

@app.get("/api/catalog")
def get_catalog():
    return {
        "status": "success",
        "message": "API Catalog is active and fully documented."
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


def _compute_overall_risk(discovered: list, missing_headers: list, open_cors: bool, server_leak: str | None) -> str:
    severities = {ep["severity"] for ep in discovered}
    if "CRITICAL" in severities:
        return "CRITICAL"
    if "HIGH" in severities or len(missing_headers) >= 4:
        return "HIGH"
    if "MEDIUM" in severities or open_cors or missing_headers or server_leak:
        return "MEDIUM"
    return "LOW"


@app.post("/api/scan-external")
def scan_external(req: ExternalScanRequest):
    """External URL Scanner — probe any public URL for security misconfigurations."""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Provide a URL to scan.")

    scan_timestamp = datetime.utcnow().isoformat() + "Z"
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    uses_https = parsed.scheme.lower() == "https"

    # ── Step 1: Fetch the target URL ──
    try:
        t_start = time.monotonic()
        resp = req_lib.get(url, timeout=10, allow_redirects=True)
        response_time_ms = round((time.monotonic() - t_start) * 1000)
        status_code = resp.status_code
        headers = dict(resp.headers)
        reachable = True
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

    # ── Step 2: Security header checks ──
    headers_lower = {k.lower(): v for k, v in headers.items()}
    missing_security_headers = [
        h for h in _SECURITY_HEADERS
        if h.lower() not in headers_lower
    ]

    # ── Step 3: CORS check ──
    open_cors = headers_lower.get("access-control-allow-origin", "") == "*"

    # ── Step 4: Server header tech leak ──
    server_val = headers_lower.get("server", "")
    server_header_leak = None
    if server_val:
        sl = server_val.lower()
        if any(kw in sl for kw in _SERVER_TECH_KEYWORDS) or len(server_val) > 3:
            server_header_leak = server_val

    # ── Step 5: Probe shadow paths ──
    discovered_endpoints = []
    for path in _SHADOW_PATHS:
        probe_url = base_url + path
        try:
            t0 = time.monotonic()
            pr = req_lib.get(
                probe_url, timeout=5,
                allow_redirects=False,
                headers={"User-Agent": "Lazarus-Scanner/2.0"},
            )
            probe_time = round((time.monotonic() - t0) * 1000)
            if pr.status_code not in (404, 410):
                classification = _classify_endpoint(pr.status_code)
                discovered_endpoints.append({
                    "path": path,
                    "status_code": pr.status_code,
                    "response_time_ms": probe_time,
                    "classification": classification["classification"],
                    "severity": classification["severity"],
                })
        except Exception:
            pass  # Timed-out or refused — not an exposed endpoint

    # ── Step 6: Overall risk ──
    overall_risk = _compute_overall_risk(
        discovered_endpoints, missing_security_headers, open_cors, server_header_leak
    )

    # ── Step 7: Plain-English summary ──
    issues = []
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
        "overall_risk": overall_risk,
        "summary": summary,
    }


@app.get("/api/compliance-report")
def get_compliance_report(api_id: str = None, path: str = None):
    """Generate a compliance report for a decommissioned API."""
    logs = db.get_all_decommissions()
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


@app.get("/api/db-status")
def db_status():
    """Check MongoDB connection status."""
    return {"connected": db.is_connected(), "uri": "mongodb://127.0.0.1:27017/lazarus"}


# ── AI Interpretation Layer Endpoints ──

class AiApiRequest(BaseModel):
    api_id: str | None = None
    path: str | None = None


class AiQueryRequest(BaseModel):
    question: str


class AiChatRequest(BaseModel):
    """Request model for the OpenRouter-powered chat endpoint."""
    question: str
    history: list = []   # list of {"role": "user"|"assistant", "content": "..."}


def _gather_all_api_details():
    """Gather full detail for every known API (catalog + shadow)."""
    all_details = []
    for api in EXPECTED_CATALOG:
        detail = get_api_detail(api_id=api["id"])
        if detail:
            all_details.append(detail)
    # Shadow APIs from traffic
    catalog_paths = {api["path"] for api in EXPECTED_CATALOG}
    for flow in LIVE_TRAFFIC_FLOW:
        if flow["path"] not in catalog_paths:
            detail = get_api_detail(path=flow["path"])
            if detail:
                all_details.append(detail)
    return all_details


@app.post("/api/ai/explain-risk")
def ai_explain_risk(req: AiApiRequest):
    """AI Risk Explanation — plain-English risk translation for non-technical users."""
    if not req.api_id and not req.path:
        raise HTTPException(status_code=400, detail="Provide api_id or path.")
    detail = get_api_detail(api_id=req.api_id, path=req.path)
    if not detail:
        raise HTTPException(status_code=404, detail="API not found.")
    result = ai_engine.explain_risk(detail)
    return {"api_path": detail.get("path"), "explanation": result}


@app.post("/api/ai/query")
def ai_query(req: AiQueryRequest):
    """Natural Language Security Query — ask questions in plain English (local engine)."""
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Provide a question.")
    all_details = _gather_all_api_details()
    analysis = analyze_api_discrepancies(EXPECTED_CATALOG, LIVE_TRAFFIC_FLOW)
    result = ai_engine.query_security(req.question, all_details, analysis)
    return {"question": req.question, "answer": result}


@app.post("/api/ai/chat")
def ai_chat(req: AiChatRequest):
    """
    OpenRouter / Qwen-powered conversational AI chat.

    This is the trial endpoint that replaces the local keyword-matching engine
    with a real LLM for free-text queries. The entire API security context is
    injected into the system prompt so the model can answer intelligently.

    Configure in .env:
        OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx
        OPENROUTER_MODEL=qwen/qwen3-235b-a22b:free
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Provide a question.")
    all_details = _gather_all_api_details()
    analysis = analyze_api_discrepancies(EXPECTED_CATALOG, LIVE_TRAFFIC_FLOW)
    answer = openrouter_engine.chat_with_openrouter(
        question=req.question,
        api_data=all_details,
        analysis=analysis,
        history=req.history,
    )
    return {"question": req.question, "answer": answer}


@app.post("/api/ai/generate-report")
def ai_generate_report(req: AiApiRequest):
    """AI Security Report Generator — comprehensive compliance report."""
    if not req.api_id and not req.path:
        raise HTTPException(status_code=400, detail="Provide api_id or path.")
    detail = get_api_detail(api_id=req.api_id, path=req.path)
    if not detail:
        raise HTTPException(status_code=404, detail="API not found.")
    result = ai_engine.generate_report(detail)
    return {"api_path": detail.get("path"), "report": result}


@app.post("/api/ai/attack-simulation")
def ai_attack_simulation(req: AiApiRequest):
    """Attack Scenario Simulator — hypothetical attack vectors."""
    if not req.api_id and not req.path:
        raise HTTPException(status_code=400, detail="Provide api_id or path.")
    detail = get_api_detail(api_id=req.api_id, path=req.path)
    if not detail:
        raise HTTPException(status_code=404, detail="API not found.")
    result = ai_engine.simulate_attack(detail)
    return {"api_path": detail.get("path"), "simulation": result}


@app.get("/api/ai/security-summary")
def ai_security_summary():
    """AI Security Summary — executive overview for dashboard."""
    all_details = _gather_all_api_details()
    analysis = analyze_api_discrepancies(EXPECTED_CATALOG, LIVE_TRAFFIC_FLOW)
    result = ai_engine.security_summary(all_details, analysis)
    return {"summary": result}


if __name__ == "__main__":
    import uvicorn
    print("\n🔒 Lazarus — Zombie API Discovery & Defence")
    print(f"   MongoDB: {'✅ Connected' if db.is_connected() else '❌ Not connected'}")
    print(f"   Persisted decommissions: {len(db.get_all_decommissions())}")
    print(f"   Persisted honeypots: {len(db.get_all_honeypots())}")
    print(f"   AI Engine: ✅ Local Engine Active")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000)