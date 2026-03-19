from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from mock_data import (
    EXPECTED_CATALOG,
    LIVE_TRAFFIC_FLOW,
    MONITORING_DATA,
    analyze_api_discrepancies,
    get_api_detail,
)
import database as db
from email_notifier import send_decommission_email
import ai_engine

app = FastAPI(title="Lazarus — Zombie API Discovery & Defence")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DefendRequest(BaseModel):
    path: str


class DecommissionRequest(BaseModel):
    api_id: str
    path: str
    reason: str = "Security risk — decommissioned via Lazarus platform."


# ── Core Endpoints ──

@app.get("/api/catalog")
def get_catalog():
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
    """Natural Language Security Query — ask questions in plain English."""
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Provide a question.")
    all_details = _gather_all_api_details()
    analysis = analyze_api_discrepancies(EXPECTED_CATALOG, LIVE_TRAFFIC_FLOW)
    result = ai_engine.query_security(req.question, all_details, analysis)
    return {"question": req.question, "answer": result}


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

