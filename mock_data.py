# mock_data.py — Lazarus: Zombie API Discovery & Defence Platform

from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# EXPECTED API CATALOG (from OpenAPI / Swagger docs)
# ═══════════════════════════════════════════════════════════════
EXPECTED_CATALOG = [
    {
        "id": "API-BNK-001",
        "path": "/api/v2/secure-transfer",
        "method": "POST",
        "name": "Secure Transfer API",
        "description": "Handles secure inter-account fund transfers with multi-factor verification.",
        "version": "v2",
        "owner": "Payments Team",
        "department": "Core Banking",
        "is_deprecated": False,
        "last_updated": "2025-10-15T08:30:00Z",
        "created_at": "2023-03-20T10:00:00Z",
    },
    {
        "id": "API-BNK-002",
        "path": "/api/v2/payments",
        "method": "POST",
        "name": "Payments Processing API",
        "description": "Processes domestic and international payment transactions.",
        "version": "v2",
        "owner": "Payments Team",
        "department": "Core Banking",
        "is_deprecated": False,
        "last_updated": "2025-11-20T14:00:00Z",
        "created_at": "2022-08-10T09:00:00Z",
    },
    {
        "id": "API-BNK-003",
        "path": "/api/v3/experimental/crypto-swap",
        "method": "PUT",
        "name": "Crypto Swap API (Experimental)",
        "description": "Experimental cryptocurrency swap endpoint — never went to production.",
        "version": "v3-experimental",
        "owner": "Innovation Lab",
        "department": "R&D",
        "is_deprecated": False,
        "last_updated": "2026-02-01T09:15:00Z",
        "created_at": "2025-12-01T13:00:00Z",
    },
    {
        "id": "API-BNK-004",
        "path": "/api/v1/legacy/auth-token",
        "method": "GET",
        "name": "Legacy Auth Token API",
        "description": "Legacy authentication token endpoint from v1 infrastructure. Marked deprecated in 2021.",
        "version": "v1",
        "owner": "Identity Team (Dissolved)",
        "department": "Security",
        "is_deprecated": True,
        "last_updated": "2021-06-10T11:45:00Z",
        "created_at": "2018-01-15T08:00:00Z",
    },
]

# ═══════════════════════════════════════════════════════════════
# LIVE TRAFFIC FLOW (from eBPF / API Gateway telemetry)
# ═══════════════════════════════════════════════════════════════
LIVE_TRAFFIC_FLOW = [
    {
        "path": "/api/v2/secure-transfer",
        "method": "POST",
        "hit_count": 84500,
        "avg_latency": "112ms",
        "error_rate": "0.02%",
        "last_seen": "2026-03-07T22:50:00Z",
        "request_source_ips": ["198.51.100.4", "203.0.113.42", "192.0.2.15"],
        "response_codes": {"200": 83800, "400": 520, "500": 180},
    },
    {
        "path": "/api/v2/payments",
        "method": "POST",
        "hit_count": 150200,
        "avg_latency": "85ms",
        "error_rate": "0.01%",
        "last_seen": "2026-03-07T22:55:00Z",
        "request_source_ips": ["198.51.100.99", "192.0.2.88", "10.45.2.1"],
        "response_codes": {"200": 149900, "400": 200, "500": 100},
    },
    {
        "path": "/api/v3/experimental/crypto-swap",
        "method": "PUT",
        "hit_count": 0,
        "avg_latency": "0ms",
        "error_rate": "0%",
        "last_seen": None,
        "request_source_ips": [],
        "response_codes": {},
    },
    {
        "path": "/api/v1/legacy/auth-token",
        "method": "GET",
        "hit_count": 412000,
        "avg_latency": "340ms",
        "error_rate": "12.4%",
        "last_seen": "2026-03-07T22:58:00Z",
        "request_source_ips": ["10.0.0.15", "10.0.0.16", "10.0.0.22"],
        "response_codes": {"200": 360880, "401": 41120, "500": 10000},
    },
    {
        # Shadow API — in traffic but not in catalog
        "path": "/api/v1/internal/admin-bypass",
        "method": "POST",
        "hit_count": 1337,
        "avg_latency": "12ms",
        "error_rate": "0%",
        "last_seen": "2026-03-07T22:45:00Z",
        "request_source_ips": ["10.99.0.5", "10.99.0.6", "10.99.0.250"],
        "response_codes": {"200": 1337},
    },
]

# ═══════════════════════════════════════════════════════════════
# SECURITY POSTURE ASSESSMENTS (per API)
# ═══════════════════════════════════════════════════════════════
SECURITY_POSTURES = {
    "API-BNK-001": {
        "overall_score": 92,
        "risk_level": "LOW",
        "authentication": {
            "status": "pass",
            "type": "OAuth 2.0 + JWT",
            "mfa_enabled": True,
            "details": "Uses OAuth 2.0 with short-lived JWT tokens (15-min expiry). MFA enforced for transfers above ₹50,000.",
        },
        "encryption": {
            "status": "pass",
            "protocol": "TLS 1.3",
            "certificate_expiry": "2027-01-15",
            "details": "End-to-end encryption with TLS 1.3. Certificate managed via automated renewal.",
        },
        "rate_limiting": {
            "status": "pass",
            "limit": "100 req/min per client",
            "burst": "150 req/min",
            "details": "Rate limiting enforced at API gateway level. DDoS mitigation active.",
        },
        "data_exposure": {
            "status": "pass",
            "risk": "low",
            "pii_fields": ["account_number (masked)", "beneficiary_name"],
            "details": "Sensitive fields are masked in responses. No raw PII exposure detected.",
        },
        "input_validation": {
            "status": "pass",
            "details": "Input sanitization and schema validation enforced. SQL injection and XSS protections active.",
        },
    },
    "API-BNK-002": {
        "overall_score": 88,
        "risk_level": "LOW",
        "authentication": {
            "status": "pass",
            "type": "OAuth 2.0 + API Key",
            "mfa_enabled": False,
            "details": "OAuth 2.0 with API key authentication. MFA not required for standard payments.",
        },
        "encryption": {
            "status": "pass",
            "protocol": "TLS 1.3",
            "certificate_expiry": "2027-03-20",
            "details": "TLS 1.3 encryption active. Certificate auto-renewed.",
        },
        "rate_limiting": {
            "status": "pass",
            "limit": "200 req/min per client",
            "burst": "300 req/min",
            "details": "Rate limiting configured. Higher limits for premium merchant accounts.",
        },
        "data_exposure": {
            "status": "warning",
            "risk": "medium",
            "pii_fields": ["card_number (partially masked)", "billing_address", "email"],
            "details": "Billing address and email are returned in full in payment confirmation responses. Recommend masking.",
        },
        "input_validation": {
            "status": "pass",
            "details": "Schema validation active. Parameterized queries prevent injection attacks.",
        },
    },
    "API-BNK-003": {
        "overall_score": 34,
        "risk_level": "MEDIUM",
        "authentication": {
            "status": "warning",
            "type": "Basic Auth (hardcoded)",
            "mfa_enabled": False,
            "details": "Uses hardcoded basic auth credentials from development phase. Never migrated to OAuth.",
        },
        "encryption": {
            "status": "warning",
            "protocol": "TLS 1.2",
            "certificate_expiry": "2026-04-01",
            "details": "Uses TLS 1.2 instead of 1.3. Certificate approaching expiry with no renewal scheduled.",
        },
        "rate_limiting": {
            "status": "fail",
            "limit": "None",
            "burst": "None",
            "details": "No rate limiting configured. Endpoint is fully open to abuse if discovered.",
        },
        "data_exposure": {
            "status": "fail",
            "risk": "high",
            "pii_fields": ["wallet_address", "private_key_fragment", "user_id"],
            "details": "⚠ CRITICAL: Response includes partial private key fragments. This is a severe data leak risk.",
        },
        "input_validation": {
            "status": "fail",
            "details": "No input validation. Raw user input is passed directly to the backend service.",
        },
    },
    "API-BNK-004": {
        "overall_score": 15,
        "risk_level": "CRITICAL",
        "authentication": {
            "status": "fail",
            "type": "Legacy Token (no expiry)",
            "mfa_enabled": False,
            "details": "Uses legacy token system with NO expiry. Tokens from 2018 are still valid. 41,120 unauthorized attempts detected.",
        },
        "encryption": {
            "status": "fail",
            "protocol": "TLS 1.0 (deprecated)",
            "certificate_expiry": "2024-12-31 (EXPIRED)",
            "details": "⚠ CRITICAL: Uses deprecated TLS 1.0. SSL certificate expired on Dec 31, 2024. Vulnerable to POODLE & BEAST attacks.",
        },
        "rate_limiting": {
            "status": "fail",
            "limit": "None",
            "burst": "None",
            "details": "No rate limiting. Currently handling 412,000 requests — possible credential stuffing attack vector.",
        },
        "data_exposure": {
            "status": "fail",
            "risk": "critical",
            "pii_fields": ["auth_token", "user_id", "session_id", "internal_ip"],
            "details": "⚠ CRITICAL: Exposes raw auth tokens, session IDs, and internal network IPs in responses.",
        },
        "input_validation": {
            "status": "fail",
            "details": "No input validation. Endpoint is vulnerable to injection attacks. Legacy code has not been patched since 2021.",
        },
    },
}

# Shadow API — no catalog entry, so we generate posture dynamically
SHADOW_API_POSTURE = {
    "/api/v1/internal/admin-bypass": {
        "overall_score": 8,
        "risk_level": "CRITICAL",
        "authentication": {
            "status": "fail",
            "type": "None (Unauthenticated)",
            "mfa_enabled": False,
            "details": "⚠ CRITICAL: No authentication whatsoever. Anyone with network access can invoke this endpoint.",
        },
        "encryption": {
            "status": "warning",
            "protocol": "TLS 1.2",
            "certificate_expiry": "Unknown",
            "details": "Uses TLS 1.2 but certificate origin is unknown. Possibly self-signed.",
        },
        "rate_limiting": {
            "status": "fail",
            "limit": "None",
            "burst": "None",
            "details": "No rate limiting. 1,337 requests from 3 internal IPs suggest automated scripted access.",
        },
        "data_exposure": {
            "status": "fail",
            "risk": "critical",
            "pii_fields": ["admin_credentials", "database_connection_string", "internal_api_keys"],
            "details": "⚠ CRITICAL: Endpoint returns admin-level credentials and database connection strings.",
        },
        "input_validation": {
            "status": "fail",
            "details": "No input validation. Accepts arbitrary payloads. Potential remote code execution vector.",
        },
    }
}

# ═══════════════════════════════════════════════════════════════
# CLASSIFICATION REASONING & RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════
CLASSIFICATIONS = {
    "API-BNK-001": {
        "type": "ACTIVE",
        "label": "Active & Verified",
        "reasoning": [
            "API is documented in the official OpenAPI catalog (v2).",
            "Receives consistent, healthy traffic: 84,500 hits with 112ms avg latency.",
            "Low error rate (0.02%) indicates stable operation.",
            "Last updated October 2025 — actively maintained by Payments Team.",
            "Security posture score: 92/100 — meets all compliance requirements.",
        ],
        "recommendations": [
            {"priority": "low", "action": "Continue monitoring traffic patterns for anomalies."},
            {"priority": "low", "action": "Schedule next security audit for Q2 2026."},
            {"priority": "info", "action": "Consider upgrading to v3 API specification when available."},
        ],
    },
    "API-BNK-002": {
        "type": "ACTIVE",
        "label": "Active & Verified",
        "reasoning": [
            "API is documented and actively maintained in the catalog.",
            "Highest traffic endpoint: 150,200 hits with excellent 85ms latency.",
            "Very low error rate (0.01%) — production-grade stability.",
            "Owned by Payments Team with regular update schedule.",
        ],
        "recommendations": [
            {"priority": "medium", "action": "Mask billing_address and email in payment confirmation responses to reduce PII exposure."},
            {"priority": "low", "action": "Consider enabling MFA for high-value payment transactions."},
            {"priority": "info", "action": "Review rate limiting thresholds for premium merchant accounts."},
        ],
    },
    "API-BNK-003": {
        "type": "STALE",
        "label": "Stale / Inactive",
        "reasoning": [
            "API is documented in catalog but receives ZERO traffic.",
            "Experimental endpoint created by Innovation Lab — never reached production.",
            "Uses hardcoded basic auth credentials from development phase.",
            "No rate limiting configured — open to abuse if discovered.",
            "Contains critical data exposure risk (private key fragments in response).",
            "Security posture score: 34/100 — fails multiple security checks.",
        ],
        "recommendations": [
            {"priority": "critical", "action": "Immediately remove private key fragments from response schema."},
            {"priority": "high", "action": "Decommission this endpoint — it serves no production purpose and poses security risks."},
            {"priority": "high", "action": "Revoke hardcoded basic auth credentials."},
            {"priority": "medium", "action": "Archive the API documentation and notify Innovation Lab."},
        ],
    },
    "API-BNK-004": {
        "type": "ZOMBIE",
        "label": "Zombie API — Deprecated but Active",
        "reasoning": [
            "⚠ API was marked DEPRECATED in June 2021 but still receives 412,000 active requests.",
            "The owning team (Identity Team) has been DISSOLVED — no one maintains this endpoint.",
            "Uses legacy token authentication with NO TOKEN EXPIRY — tokens from 2018 still work.",
            "SSL certificate EXPIRED on Dec 31, 2024 — using deprecated TLS 1.0.",
            "12.4% error rate with 41,120 unauthorized (401) responses — possible credential stuffing.",
            "High latency (340ms) indicates degraded infrastructure.",
            "Security posture score: 15/100 — CRITICAL risk to the organization.",
        ],
        "recommendations": [
            {"priority": "critical", "action": "Immediately rotate all legacy auth tokens and invalidate 2018-era credentials."},
            {"priority": "critical", "action": "Upgrade or terminate TLS 1.0 — vulnerable to POODLE and BEAST attacks."},
            {"priority": "critical", "action": "Investigate 41,120 unauthorized requests for credential stuffing patterns."},
            {"priority": "high", "action": "Deploy API honeypot to monitor and trap malicious traffic before decommissioning."},
            {"priority": "high", "action": "Identify and migrate all legitimate consumers to the v2 auth endpoint."},
            {"priority": "medium", "action": "Execute full decommissioning workflow with traffic rerouting plan."},
        ],
    },
}

SHADOW_CLASSIFICATION = {
    "/api/v1/internal/admin-bypass": {
        "type": "SHADOW",
        "label": "Shadow API — Undocumented Backdoor",
        "reasoning": [
            "⚠ CRITICAL: This endpoint exists in live traffic but is NOT in any API catalog or documentation.",
            "Receives 1,337 requests exclusively from 3 internal IPs (10.99.0.x subnet).",
            "Extremely low latency (12ms) suggests it directly accesses internal systems.",
            "100% success rate (all 200 responses) — no authentication failures means NO AUTH.",
            "The 'admin-bypass' path name strongly suggests an intentional backdoor.",
            "No known team or department owns this endpoint.",
            "Possible insider threat or residual dev/debug endpoint left in production.",
        ],
        "recommendations": [
            {"priority": "critical", "action": "Immediately block all traffic to this endpoint at the API gateway level."},
            {"priority": "critical", "action": "Investigate the 3 source IPs (10.99.0.5, 10.99.0.6, 10.99.0.250) — identify who/what is making these requests."},
            {"priority": "critical", "action": "Review code repositories for the source code of this endpoint."},
            {"priority": "critical", "action": "Conduct security incident response — treat as potential insider threat."},
            {"priority": "high", "action": "Audit all internal subnets for similar undocumented endpoints."},
            {"priority": "high", "action": "Deploy honeypot to capture request payloads before blocking."},
        ],
    }
}

# ═══════════════════════════════════════════════════════════════
# MONITORING DATA
# ═══════════════════════════════════════════════════════════════
MONITORING_DATA = {
    "scan_status": "active",
    "last_full_scan": "2026-03-07T22:50:00Z",
    "next_scan": "2026-03-07T23:50:00Z",
    "scan_interval": "60 minutes",
    "total_scans_today": 23,
    "apis_discovered_today": 0,
    "networks_scanned": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
    "gateways_monitored": ["Kong API Gateway", "AWS API Gateway", "Internal Nginx Proxy"],
    "repositories_scanned": 47,
    "deployment_envs": ["production", "staging", "dev"],
    "scan_history": [
        {"timestamp": "2026-03-07T22:50:00Z", "apis_found": 5, "new_threats": 0, "status": "clean"},
        {"timestamp": "2026-03-07T21:50:00Z", "apis_found": 5, "new_threats": 0, "status": "clean"},
        {"timestamp": "2026-03-07T20:50:00Z", "apis_found": 5, "new_threats": 1, "status": "alert"},
        {"timestamp": "2026-03-07T19:50:00Z", "apis_found": 5, "new_threats": 0, "status": "clean"},
        {"timestamp": "2026-03-07T18:50:00Z", "apis_found": 4, "new_threats": 0, "status": "clean"},
        {"timestamp": "2026-03-07T17:50:00Z", "apis_found": 4, "new_threats": 0, "status": "clean"},
        {"timestamp": "2026-03-07T16:50:00Z", "apis_found": 4, "new_threats": 0, "status": "clean"},
        {"timestamp": "2026-03-07T15:50:00Z", "apis_found": 4, "new_threats": 1, "status": "alert"},
    ],
    "threat_timeline": [
        {"date": "2026-03-07", "shadow": 1, "zombie": 1, "stale": 1},
        {"date": "2026-03-06", "shadow": 1, "zombie": 1, "stale": 1},
        {"date": "2026-03-05", "shadow": 0, "zombie": 1, "stale": 1},
        {"date": "2026-03-04", "shadow": 0, "zombie": 1, "stale": 2},
        {"date": "2026-03-03", "shadow": 0, "zombie": 2, "stale": 2},
        {"date": "2026-03-02", "shadow": 0, "zombie": 2, "stale": 2},
        {"date": "2026-03-01", "shadow": 0, "zombie": 2, "stale": 3},
    ],
}

# ═══════════════════════════════════════════════════════════════
# DECOMMISSION LOG
# ═══════════════════════════════════════════════════════════════
DECOMMISSION_LOG = []

# ═══════════════════════════════════════════════════════════════
# ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════
def analyze_api_discrepancies(catalog, traffic):
    catalog_paths = {api["path"]: api for api in catalog}
    traffic_paths = {flow["path"]: flow for flow in traffic}

    discrepancies = {"shadow_apis": [], "zombie_apis": [], "stale_apis": []}

    for flow in traffic:
        if flow["path"] not in catalog_paths:
            discrepancies["shadow_apis"].append(flow["path"])

    for api in catalog:
        path = api["path"]
        flow = traffic_paths.get(path)
        if flow:
            if api["is_deprecated"] and flow["hit_count"] > 0:
                discrepancies["zombie_apis"].append(path)
            if not api["is_deprecated"] and flow["hit_count"] == 0:
                discrepancies["stale_apis"].append(path)
        else:
            if not api["is_deprecated"]:
                discrepancies["stale_apis"].append(path)

    return discrepancies


def get_api_detail(api_id=None, path=None):
    """Get full detail for an API by ID or path."""
    api_entry = None

    if api_id:
        for api in EXPECTED_CATALOG:
            if api["id"] == api_id:
                api_entry = api
                break

    if path and not api_entry:
        for api in EXPECTED_CATALOG:
            if api["path"] == path:
                api_entry = api
                break

    # Shadow API (not in catalog)
    if not api_entry and path:
        flow = next((f for f in LIVE_TRAFFIC_FLOW if f["path"] == path), None)
        if flow:
            posture = SHADOW_API_POSTURE.get(path, {})
            classification = SHADOW_CLASSIFICATION.get(path, {})
            return {
                "id": "SHADOW-" + path.replace("/", "-").strip("-"),
                "path": path,
                "method": flow["method"],
                "name": "Unknown / Undocumented Endpoint",
                "description": "This endpoint was discovered in live network traffic but does not exist in any API catalog or documentation.",
                "version": "Unknown",
                "owner": "Unknown — No team ownership identified",
                "department": "Unknown",
                "is_deprecated": False,
                "last_updated": None,
                "created_at": None,
                "status": "SHADOW",
                "traffic": flow,
                "security_posture": posture,
                "classification": classification,
                "is_in_catalog": False,
            }

    if not api_entry:
        return None

    aid = api_entry["id"]
    flow = next((f for f in LIVE_TRAFFIC_FLOW if f["path"] == api_entry["path"]), None)
    posture = SECURITY_POSTURES.get(aid, {})
    classification = CLASSIFICATIONS.get(aid, {})

    # Determine status
    status = "ACTIVE"
    if api_entry["is_deprecated"] and flow and flow["hit_count"] > 0:
        status = "ZOMBIE"
    elif not flow or flow.get("hit_count", 0) == 0:
        status = "STALE"

    return {
        **api_entry,
        "status": status,
        "traffic": flow,
        "security_posture": posture,
        "classification": classification,
        "is_in_catalog": True,
    }


if __name__ == "__main__":
    import json
    results = analyze_api_discrepancies(EXPECTED_CATALOG, LIVE_TRAFFIC_FLOW)
    print(json.dumps(results, indent=2))
