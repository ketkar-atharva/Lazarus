"""
AI Interpretation Layer for Lazarus — Zombie API Discovery & Defence.

Fully local, rule-based + context-aware AI engine.
No external API dependencies. Uses project security data to generate
intelligent, human-like responses.

Powers:
  1. AI Risk Explanation Engine
  2. Natural Language Security Queries
  3. Automated Security Report Generator
  4. Attack Scenario Simulator
  5. Executive Security Summary
"""

import json
import time
import random


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _safe_json(data):
    """Convert data to JSON string, handling non-serializable types."""
    def default(o):
        return str(o)
    return json.dumps(data, indent=2, default=default)


def _simulated_delay():
    """Add a small delay to simulate AI thinking time for better UX."""
    time.sleep(random.uniform(0.3, 0.8))


def _get_risk_emoji(risk_level):
    """Return emoji for risk level."""
    mapping = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢",
    }
    return mapping.get(risk_level.upper() if risk_level else "", "⚪")


def _get_status_emoji(status):
    """Return emoji for check status."""
    mapping = {"pass": "✅", "warning": "⚠️", "fail": "❌"}
    return mapping.get(status, "❓")


def _find_apis_by_condition(all_apis, condition_fn):
    """Filter APIs by a condition function."""
    return [api for api in all_apis if condition_fn(api)]


# ═══════════════════════════════════════════════════════════════
# 1. AI RISK EXPLANATION ENGINE
# ═══════════════════════════════════════════════════════════════

def explain_risk(api_detail: dict) -> str:
    """
    Translate complex API security findings into clear, business-friendly
    risk explanations for non-technical banking employees.
    """
    _simulated_delay()

    name = api_detail.get("name", "Unknown API")
    path = api_detail.get("path", "Unknown")
    posture = api_detail.get("security_posture", {})
    score = posture.get("overall_score", "N/A")
    risk_level = posture.get("risk_level", "UNKNOWN")
    classification = api_detail.get("classification", {})
    api_type = classification.get("type", "UNKNOWN")
    status = api_detail.get("status", "UNKNOWN")

    # Build findings list
    findings = []
    recommendations = []

    auth = posture.get("authentication", {})
    if auth.get("status") == "fail":
        findings.append(f"- **Authentication is BROKEN** — {auth.get('details', 'No details')}. "
                        "Think of this as leaving the vault door wide open — anyone who finds it can walk in.")
        recommendations.append("🔧 Immediately implement proper authentication (OAuth 2.0 with JWT tokens)")
    elif auth.get("status") == "warning":
        findings.append(f"- **Authentication is WEAK** — {auth.get('details', '')}. "
                        "This is like having a lock that uses the same key for everyone.")
        recommendations.append("🔧 Upgrade authentication to OAuth 2.0 and remove hardcoded credentials")

    enc = posture.get("encryption", {})
    if enc.get("status") == "fail":
        findings.append(f"- **Encryption is BROKEN** — {enc.get('details', '')}. "
                        "Customer data is being sent over an insecure connection — like sending bank statements on a postcard.")
        recommendations.append("🔧 Upgrade to TLS 1.3 and renew expired certificates immediately")
    elif enc.get("status") == "warning":
        findings.append(f"- **Encryption needs attention** — {enc.get('details', '')}.")
        recommendations.append("🔧 Plan TLS upgrade to version 1.3")

    rl = posture.get("rate_limiting", {})
    if rl.get("status") == "fail":
        findings.append("- **No rate limiting** — Anyone can flood this API with unlimited requests. "
                        "This is like having no queue management at a bank branch — chaos.")
        recommendations.append("🔧 Configure rate limiting at the API gateway (e.g., 100 req/min)")

    de = posture.get("data_exposure", {})
    if de.get("status") == "fail":
        pii = ", ".join(de.get("pii_fields", []))
        findings.append(f"- **Sensitive data is EXPOSED** — The API reveals: {pii}. "
                        "This is like printing customer account details on the bank's public noticeboard.")
        recommendations.append("🔧 Mask or remove sensitive fields from API responses immediately")
    elif de.get("status") == "warning":
        pii = ", ".join(de.get("pii_fields", []))
        findings.append(f"- **Some data exposure risk** — Fields like {pii} are partially visible in responses.")
        recommendations.append("🔧 Review and mask PII fields in API responses")

    iv = posture.get("input_validation", {})
    if iv.get("status") == "fail":
        findings.append(f"- **No input validation** — {iv.get('details', '')}. "
                        "This is like accepting any document at the counter without checking if it's genuine.")
        recommendations.append("🔧 Implement input validation and sanitization")

    risk_emoji = _get_risk_emoji(risk_level)
    findings_text = "\n".join(findings) if findings else "- No critical findings detected. This API appears well-secured."
    recs_text = "\n".join(recommendations) if recommendations else "- Continue regular security monitoring."

    result = f"""# {risk_emoji} Risk Analysis: {name}

**API Path:** `{path}` | **Security Score:** {score}/100 | **Risk Level:** {risk_emoji} {risk_level}

## 📋 What is this API?
{api_detail.get("description", "No description available.")}

## ⚠️ What's Wrong?
{findings_text}

## 💰 Why Should You Care? (Business Impact)
"""

    if risk_level == "CRITICAL":
        result += ("This API poses an **immediate threat** to the bank. Vulnerabilities at this level "
                   "could lead to **unauthorized access to customer accounts**, **regulatory fines from RBI**, "
                   "and **severe reputation damage**. Every day this remains unfixed increases our exposure.\n\n")
    elif risk_level == "MEDIUM":
        result += ("This API has **moderate security gaps** that could be exploited by a determined attacker. "
                   "While not immediately critical, these issues should be addressed within the next sprint "
                   "to prevent escalation.\n\n")
    elif risk_level == "LOW":
        result += ("This API is **well-secured** and meets compliance requirements. Continue monitoring "
                   "for any changes in traffic patterns or new vulnerabilities.\n\n")
    else:
        result += "Risk assessment is pending further analysis.\n\n"

    result += f"""## ✅ What Should We Do?
{recs_text}

---
*Analysis generated by Lazarus Local AI Engine using real-time security scan data.*"""

    return result


# ═══════════════════════════════════════════════════════════════
# 2. NATURAL LANGUAGE SECURITY QUERIES
# ═══════════════════════════════════════════════════════════════

def generate_local_response(question: str, api_data: list, analysis: dict) -> str:
    """
    Analyze user question using keyword matching and search through API data
    to return structured, human-like responses.
    """
    q = question.lower().strip()

    # ── No Authentication ──
    if any(kw in q for kw in ["no auth", "no authentication", "without auth", "unauthenticated",
                               "missing auth", "failed auth", "broken auth"]):
        failed_auth = _find_apis_by_condition(api_data, lambda a:
            a.get("security_posture", {}).get("authentication", {}).get("status") == "fail")
        if failed_auth:
            lines = []
            for api in failed_auth:
                auth_detail = api.get("security_posture", {}).get("authentication", {})
                lines.append(f"- **{api.get('name', 'Unknown')}** (`{api.get('path', '')}`) — "
                             f"{auth_detail.get('details', 'No authentication configured')}")
            return (f"## 🔓 APIs With Authentication Failures\n\n"
                    f"I found **{len(failed_auth)} API(s)** with broken or missing authentication:\n\n"
                    + "\n".join(lines) +
                    "\n\n> **⚡ Recommendation:** These APIs are your highest priority. "
                    "An attacker could access them without any credentials — like an unlocked door to the vault.")
        return ("## 🔓 Authentication Check\n\n"
                "✅ Good news — all APIs in the current scan have some form of authentication configured. "
                "However, some may use weak methods (like hardcoded credentials). "
                "I recommend reviewing the full security posture in the dashboard.")

    # ── Critical Risk ──
    if any(kw in q for kw in ["critical risk", "critical", "highest risk", "most dangerous",
                               "most risky", "worst", "high risk"]):
        critical = _find_apis_by_condition(api_data, lambda a:
            a.get("security_posture", {}).get("risk_level", "").upper() == "CRITICAL")
        if critical:
            lines = []
            for api in critical:
                posture = api.get("security_posture", {})
                lines.append(f"- **{api.get('name', 'Unknown')}** (`{api.get('path', '')}`) — "
                             f"Score: {posture.get('overall_score', 'N/A')}/100, "
                             f"Status: {api.get('status', 'Unknown')}")
            return (f"## 🔴 Critical Risk APIs\n\n"
                    f"There are **{len(critical)} API(s)** at critical risk level:\n\n"
                    + "\n".join(lines) +
                    "\n\n> **⚡ Action Required:** These need immediate attention. "
                    "Critical-risk APIs can lead to data breaches, regulatory fines, and financial losses.")
        return "## 🔴 Critical Risk Check\n\n✅ No APIs are currently at critical risk level. Keep monitoring!"

    # ── Zombie APIs ──
    if any(kw in q for kw in ["zombie", "deprecated", "deprecated but active", "old api",
                               "legacy", "outdated"]):
        zombies = analysis.get("zombie_apis", [])
        if zombies:
            zombie_details = []
            for path in zombies:
                api = next((a for a in api_data if a.get("path") == path), None)
                if api:
                    traffic = api.get("traffic", {})
                    zombie_details.append(
                        f"- **{api.get('name', 'Unknown')}** (`{path}`) — "
                        f"Marked deprecated but still receiving **{traffic.get('hit_count', 0):,} requests**. "
                        f"Error rate: {traffic.get('error_rate', 'N/A')}")
            return (f"## 🧟 Zombie APIs Detected\n\n"
                    f"A **Zombie API** is an API that was officially marked as deprecated or end-of-life, "
                    f"but is still receiving live traffic. This is dangerous because:\n"
                    f"- Nobody is maintaining the code or patching security vulnerabilities\n"
                    f"- The owning team may no longer exist\n"
                    f"- Old security standards may be in use\n\n"
                    f"**Found {len(zombies)} Zombie API(s):**\n\n"
                    + "\n".join(zombie_details) +
                    "\n\n> **⚡ Recommendation:** Plan a migration path for consumers, "
                    "then decommission these APIs using the Lazarus decommission workflow.")
        return ("## 🧟 Zombie API Check\n\n"
                "✅ No zombie APIs detected! All deprecated APIs have zero traffic.")

    # ── Shadow APIs ──
    if any(kw in q for kw in ["shadow", "undocumented", "unknown", "backdoor", "hidden",
                               "unregistered"]):
        shadows = analysis.get("shadow_apis", [])
        if shadows:
            shadow_details = []
            for path in shadows:
                api = next((a for a in api_data if a.get("path") == path), None)
                if api:
                    traffic = api.get("traffic", {})
                    shadow_details.append(
                        f"- **`{path}`** — {traffic.get('hit_count', 0):,} requests, "
                        f"Latency: {traffic.get('avg_latency', 'N/A')}, "
                        f"Source IPs: {', '.join(traffic.get('request_source_ips', []))}")
            return (f"## 👻 Shadow APIs Detected\n\n"
                    f"A **Shadow API** is an endpoint found in live network traffic that does NOT exist "
                    f"in any API catalog or documentation. This could indicate:\n"
                    f"- A developer backdoor left in production\n"
                    f"- An insider threat\n"
                    f"- A debug/test endpoint that was never removed\n\n"
                    f"**Found {len(shadows)} Shadow API(s):**\n\n"
                    + "\n".join(shadow_details) +
                    "\n\n> **⚡ Recommendation:** Immediately investigate the source IPs and block traffic "
                    "at the API gateway. Treat this as a potential security incident.")
        return ("## 👻 Shadow API Check\n\n"
                "✅ No shadow APIs detected. All traffic corresponds to documented endpoints.")

    # ── Data Exposure / PII ──
    if any(kw in q for kw in ["data exposure", "pii", "sensitive data", "customer data",
                               "personal data", "data leak", "expose"]):
        exposed = _find_apis_by_condition(api_data, lambda a:
            a.get("security_posture", {}).get("data_exposure", {}).get("status") in ("fail", "warning"))
        if exposed:
            lines = []
            for api in exposed:
                de = api.get("security_posture", {}).get("data_exposure", {})
                pii = ", ".join(de.get("pii_fields", []))
                lines.append(f"- **{api.get('name', 'Unknown')}** (`{api.get('path', '')}`) — "
                             f"Risk: {de.get('risk', 'unknown').upper()}, Exposed fields: {pii}")
            return (f"## 🔍 APIs Exposing Sensitive Data\n\n"
                    f"Found **{len(exposed)} API(s)** with data exposure concerns:\n\n"
                    + "\n".join(lines) +
                    "\n\n> **⚡ Recommendation:** Mask all PII fields in responses. "
                    "Under RBI and PCI-DSS guidelines, exposing raw customer data can result in "
                    "regulatory penalties and loss of customer trust.")
        return ("## 🔍 Data Exposure Check\n\n"
                "✅ No APIs are currently exposing sensitive customer data. "
                "All PII fields are properly masked.")

    # ── Encryption / TLS ──
    if any(kw in q for kw in ["encryption", "tls", "ssl", "certificate", "https"]):
        enc_issues = _find_apis_by_condition(api_data, lambda a:
            a.get("security_posture", {}).get("encryption", {}).get("status") in ("fail", "warning"))
        if enc_issues:
            lines = []
            for api in enc_issues:
                enc = api.get("security_posture", {}).get("encryption", {})
                lines.append(f"- **{api.get('name', 'Unknown')}** (`{api.get('path', '')}`) — "
                             f"Protocol: {enc.get('protocol', 'Unknown')}, "
                             f"Certificate expiry: {enc.get('certificate_expiry', 'Unknown')}")
            return (f"## 🔐 Encryption Issues Found\n\n"
                    f"Found **{len(enc_issues)} API(s)** with encryption concerns:\n\n"
                    + "\n".join(lines) +
                    "\n\n> **⚡ Recommendation:** Upgrade all APIs to TLS 1.3 and ensure certificates "
                    "are auto-renewed before expiry.")
        return ("## 🔐 Encryption Check\n\n"
                "✅ All APIs are using secure encryption (TLS 1.3) with valid certificates.")

    # ── Payment APIs ──
    if any(kw in q for kw in ["payment", "payments", "transfer", "transaction", "fund"]):
        payment_apis = _find_apis_by_condition(api_data, lambda a:
            any(kw in (a.get("name", "") + a.get("path", "")).lower()
                for kw in ["payment", "transfer", "transaction"]))
        if payment_apis:
            lines = []
            for api in payment_apis:
                posture = api.get("security_posture", {})
                risk_emoji = _get_risk_emoji(posture.get("risk_level", ""))
                lines.append(f"- {risk_emoji} **{api.get('name', 'Unknown')}** (`{api.get('path', '')}`) — "
                             f"Score: {posture.get('overall_score', 'N/A')}/100, "
                             f"Risk: {posture.get('risk_level', 'N/A')}")
            return (f"## 💳 Payment API Security\n\n"
                    f"Found **{len(payment_apis)} payment-related API(s)**:\n\n"
                    + "\n".join(lines) +
                    "\n\n> Payment APIs handle real money — even minor vulnerabilities here "
                    "could result in direct financial losses.")
        return "## 💳 Payment APIs\n\nNo payment-related APIs found in the current scan."

    # ── Biggest security concern ──
    if any(kw in q for kw in ["biggest concern", "biggest security", "most important",
                               "top priority", "main threat", "biggest threat", "most urgent"]):
        # Find the API with the lowest security score
        worst_api = None
        worst_score = 101
        for api in api_data:
            score = api.get("security_posture", {}).get("overall_score", 100)
            if score < worst_score:
                worst_score = score
                worst_api = api
        if worst_api:
            posture = worst_api.get("security_posture", {})
            name = worst_api.get("name", "Unknown")
            path = worst_api.get("path", "")
            issues = []
            for check in ["authentication", "encryption", "rate_limiting", "data_exposure", "input_validation"]:
                detail = posture.get(check, {})
                if detail.get("status") == "fail":
                    issues.append(f"  - {_get_status_emoji('fail')} **{check.replace('_', ' ').title()}**: {detail.get('details', 'Failed')}")
            return (f"## 🚨 Biggest Security Concern\n\n"
                    f"The most critical threat right now is **{name}** (`{path}`) "
                    f"with a security score of just **{worst_score}/100**.\n\n"
                    f"**Failed security checks:**\n"
                    + "\n".join(issues) +
                    f"\n\n> **⚡ This should be your #1 priority.** "
                    f"Consider using the Lazarus decommission workflow if this API is no longer needed.")
        return "## 🚨 Security Overview\n\nAll APIs are currently within acceptable risk levels."

    # ── Stale APIs ──
    if any(kw in q for kw in ["stale", "inactive", "unused", "no traffic", "zero traffic"]):
        stales = analysis.get("stale_apis", [])
        if stales:
            stale_details = []
            for path in stales:
                api = next((a for a in api_data if a.get("path") == path), None)
                if api:
                    stale_details.append(
                        f"- **{api.get('name', 'Unknown')}** (`{path}`) — "
                        f"Last updated: {api.get('last_updated', 'Unknown')}, "
                        f"Owner: {api.get('owner', 'Unknown')}")
            return (f"## 💤 Stale / Inactive APIs\n\n"
                    f"Found **{len(stales)} API(s)** with zero traffic:\n\n"
                    + "\n".join(stale_details) +
                    "\n\n> **⚡ Recommendation:** Review whether these APIs are still needed. "
                    "Unused APIs with poor security are a liability.")
        return "## 💤 Stale API Check\n\n✅ All documented APIs are actively receiving traffic."

    # ── General / Overview ──
    if any(kw in q for kw in ["overview", "summary", "status", "how are", "overall",
                               "tell me about", "what is", "security posture"]):
        return _build_overview_response(api_data, analysis)

    # ── Fallback: intelligent generic response ──
    return _build_fallback_response(question, api_data, analysis)


def _build_overview_response(api_data, analysis):
    """Build a general overview of the security posture."""
    total = len(api_data)
    shadows = len(analysis.get("shadow_apis", []))
    zombies = len(analysis.get("zombie_apis", []))
    stales = len(analysis.get("stale_apis", []))

    critical_count = sum(1 for a in api_data
                         if a.get("security_posture", {}).get("risk_level", "").upper() == "CRITICAL")
    avg_score = sum(a.get("security_posture", {}).get("overall_score", 0)
                    for a in api_data) / max(total, 1)

    return (f"## 📊 API Security Overview\n\n"
            f"Lazarus is currently tracking **{total} APIs** across the bank's infrastructure.\n\n"
            f"| Metric | Value |\n|---|---|\n"
            f"| Total APIs | {total} |\n"
            f"| Shadow APIs | {shadows} |\n"
            f"| Zombie APIs | {zombies} |\n"
            f"| Stale APIs | {stales} |\n"
            f"| Critical Risk | {critical_count} |\n"
            f"| Avg. Security Score | {avg_score:.0f}/100 |\n\n"
            f"> Ask me about specific categories like \"zombie APIs\", \"critical risk\", "
            f"or \"data exposure\" for detailed analysis.")


def _build_fallback_response(question, api_data, analysis):
    """Return an intelligent fallback when no specific keyword matches."""
    total = len(api_data)
    critical_count = sum(1 for a in api_data
                         if a.get("security_posture", {}).get("risk_level", "").upper() == "CRITICAL")
    shadows = len(analysis.get("shadow_apis", []))
    zombies = len(analysis.get("zombie_apis", []))

    return (f"## 💬 Lazarus AI Response\n\n"
            f"I'm not sure I fully understood your question: *\"{question}\"*\n\n"
            f"Here's what I can tell you about your current security posture:\n"
            f"- **{total} APIs** are being monitored\n"
            f"- **{critical_count}** are at critical risk level\n"
            f"- **{shadows}** shadow (undocumented) APIs detected\n"
            f"- **{zombies}** zombie (deprecated but active) APIs found\n\n"
            f"**Try asking me:**\n"
            f"- \"Which APIs have no authentication?\"\n"
            f"- \"Show me all critical risk APIs\"\n"
            f"- \"What are zombie APIs?\"\n"
            f"- \"Which APIs expose sensitive customer data?\"\n"
            f"- \"What is our biggest security concern?\"\n\n"
            f"I can analyze your security data and provide detailed insights on any of these topics!")


def query_security(question: str, all_apis: list, analysis: dict) -> str:
    """Answer natural-language security questions using the local AI engine."""
    _simulated_delay()
    return generate_local_response(question, all_apis, analysis)


# ═══════════════════════════════════════════════════════════════
# 3. AUTOMATED SECURITY REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_report(api_detail: dict) -> str:
    """
    Generate a comprehensive security & compliance report for an API
    using local template-based generation.
    """
    _simulated_delay()

    name = api_detail.get("name", "Unknown API")
    path = api_detail.get("path", "Unknown")
    method = api_detail.get("method", "Unknown")
    version = api_detail.get("version", "Unknown")
    owner = api_detail.get("owner", "Unknown")
    status = api_detail.get("status", "Unknown")
    last_updated = api_detail.get("last_updated", "N/A")
    posture = api_detail.get("security_posture", {})
    score = posture.get("overall_score", "N/A")
    risk_level = posture.get("risk_level", "UNKNOWN")
    risk_emoji = _get_risk_emoji(risk_level)
    traffic = api_detail.get("traffic", {})

    # Security checks table
    checks = []
    for check_name in ["authentication", "encryption", "rate_limiting", "data_exposure", "input_validation"]:
        detail = posture.get(check_name, {})
        status_val = detail.get("status", "unknown")
        emoji = _get_status_emoji(status_val)
        checks.append(f"| {check_name.replace('_', ' ').title()} | {emoji} {status_val.upper()} "
                       f"| {detail.get('details', 'N/A')[:80]} |")

    checks_table = "\n".join(checks)

    # Immediate actions
    immediate = []
    short_term = []
    medium_term = []

    if posture.get("authentication", {}).get("status") == "fail":
        immediate.append("- 🔴 Implement proper authentication (OAuth 2.0 + JWT)")
    if posture.get("encryption", {}).get("status") == "fail":
        immediate.append("- 🔴 Upgrade to TLS 1.3 and renew expired certificates")
    if posture.get("data_exposure", {}).get("status") == "fail":
        immediate.append("- 🔴 Remove/mask all exposed PII from API responses")
    if posture.get("rate_limiting", {}).get("status") == "fail":
        short_term.append("- 🟡 Configure rate limiting at API gateway")
    if posture.get("input_validation", {}).get("status") == "fail":
        short_term.append("- 🟡 Implement input validation and sanitization")
    if posture.get("encryption", {}).get("status") == "warning":
        medium_term.append("- 🟢 Plan TLS version upgrade to 1.3")
    if posture.get("authentication", {}).get("status") == "warning":
        medium_term.append("- 🟢 Migrate from basic auth to OAuth 2.0")

    if not immediate:
        immediate.append("- ✅ No immediate actions required")
    if not short_term:
        short_term.append("- ✅ No short-term actions required")
    if not medium_term:
        medium_term.append("- ✅ No medium-term actions required")

    hit_count = traffic.get("hit_count", 0) if traffic else 0
    error_rate = traffic.get("error_rate", "0%") if traffic else "0%"
    latency = traffic.get("avg_latency", "N/A") if traffic else "N/A"

    return f"""# 🔒 API Security & Compliance Report

## Executive Summary
**{name}** (`{path}`) has a security score of **{score}/100** with a risk rating of {risk_emoji} **{risk_level}**. {"This API requires immediate security remediation before it can meet regulatory compliance standards." if risk_level in ("CRITICAL", "HIGH") else "This API meets most security requirements but should be reviewed for ongoing compliance." if risk_level == "MEDIUM" else "This API is well-secured and meets current compliance standards."}

## API Overview
| Field | Value |
|---|---|
| Name | {name} |
| Path | `{path}` |
| Method | {method} |
| Version | {version} |
| Owner | {owner} |
| Status | {status} |
| Last Updated | {last_updated} |
| Traffic Volume | {hit_count:,} requests |
| Avg Latency | {latency} |
| Error Rate | {error_rate} |

## Security Assessment
| Check | Status | Details |
|---|---|---|
{checks_table}

## Risk Analysis
- **Overall Score:** {score}/100
- **Risk Level:** {risk_emoji} {risk_level}
- **Business Impact:** {"Direct financial and regulatory exposure — requires CISO escalation" if risk_level == "CRITICAL" else "Moderate risk — should be addressed in current sprint" if risk_level == "MEDIUM" else "Low risk — standard monitoring continues"}

## Compliance Mapping
| Requirement | Status |
|---|---|
| RBI IT Framework 2023 — API Security | {"❌ Non-compliant" if risk_level in ("CRITICAL",) else "⚠️ Partially compliant" if risk_level == "MEDIUM" else "✅ Compliant"} |
| PCI-DSS v4.0 Req. 6.3.2 — Unused APIs | {"❌ Non-compliant" if status in ("ZOMBIE", "STALE") else "✅ Compliant"} |
| PCI-DSS v4.0 Req. 11.3 — Vulnerability Mgmt | {"❌ Non-compliant" if score is not None and isinstance(score, (int, float)) and score < 50 else "✅ Compliant"} |
| Data Protection Guidelines — PII | {"❌ Non-compliant" if posture.get("data_exposure", {}).get("status") == "fail" else "✅ Compliant"} |

## Remediation Roadmap

### 🔴 Immediate (within 24 hours)
{chr(10).join(immediate)}

### 🟡 Short-term (within 1 week)
{chr(10).join(short_term)}

### 🟢 Medium-term (within 1 month)
{chr(10).join(medium_term)}

## Conclusion
{"⚠️ **This API FAILS compliance requirements and poses an active threat.** Immediate remediation is required. Recommend escalation to CISO with a 24-hour remediation deadline." if risk_level == "CRITICAL" else "⚠️ This API has notable security gaps. Address the identified issues within the current sprint cycle." if risk_level == "MEDIUM" else "✅ This API meets current security and compliance standards. Continue regular monitoring and scheduled audits."}

---
*Report generated by Lazarus Local AI Engine | Confidential — For Internal Use Only*"""


# ═══════════════════════════════════════════════════════════════
# 4. ATTACK SCENARIO SIMULATOR
# ═══════════════════════════════════════════════════════════════

def simulate_attack(api_detail: dict) -> str:
    """
    Generate hypothetical attack scenarios based on actual vulnerabilities
    found in the API's security posture.
    """
    _simulated_delay()

    name = api_detail.get("name", "Unknown API")
    path = api_detail.get("path", "Unknown")
    posture = api_detail.get("security_posture", {})
    scenarios = []
    scenario_num = 1

    # Scenario: No Authentication
    auth = posture.get("authentication", {})
    if auth.get("status") == "fail":
        scenarios.append(f"""## ⚔ Attack Scenario {scenario_num}: Unauthorized Access Exploit

**Threat Actor Profile:** External hacker or malicious insider
**Difficulty Level:** Easy
**Potential Impact:** Full unauthorized access to API functionality

### Attack Steps:
1. **Discovery** — Attacker discovers `{path}` through network scanning or leaked documentation
2. **Direct Access** — Since there is no authentication, the attacker sends requests directly without any credentials
3. **Data Extraction** — Attacker systematically queries the API to extract sensitive data
4. **Lateral Movement** — Using the obtained data (credentials, tokens), attacker moves to other internal systems

### Evidence from Scan Data:
- {auth.get('details', 'Authentication is missing or broken')}

### Real-World Parallel:
- Similar to the 2019 Capital One breach where misconfigured access controls led to exposure of 100M+ customer records

### How to Prevent This:
- Implement OAuth 2.0 with JWT tokens immediately
- Add IP whitelist restrictions at the API gateway
- Deploy rate limiting to prevent automated data extraction""")
        scenario_num += 1

    # Scenario: Expired/Weak Encryption
    enc = posture.get("encryption", {})
    if enc.get("status") == "fail":
        scenarios.append(f"""## ⚔ Attack Scenario {scenario_num}: Man-in-the-Middle (MITM) Attack

**Threat Actor Profile:** Sophisticated attacker on the same network segment
**Difficulty Level:** Moderate
**Potential Impact:** Interception of all data in transit, including credentials and financial data

### Attack Steps:
1. **Network Positioning** — Attacker gains access to the same network (e.g., via compromised Wi-Fi or VPN)
2. **Traffic Interception** — Using tools like Wireshark, attacker intercepts traffic to `{path}` which uses {enc.get('protocol', 'weak encryption')}
3. **Credential Theft** — Auth tokens and session IDs are captured in plaintext
4. **Session Hijacking** — Attacker replays stolen tokens to impersonate legitimate users

### Evidence from Scan Data:
- {enc.get('details', 'Weak or deprecated encryption in use')}

### Real-World Parallel:
- The POODLE attack (2014) exploited SSL 3.0 vulnerabilities to decrypt encrypted traffic

### How to Prevent This:
- Upgrade to TLS 1.3 immediately
- Renew expired certificates with automated renewal
- Enable HSTS (HTTP Strict Transport Security)""")
        scenario_num += 1

    # Scenario: Data Exposure
    de = posture.get("data_exposure", {})
    if de.get("status") == "fail":
        pii = ", ".join(de.get("pii_fields", []))
        scenarios.append(f"""## ⚔ Attack Scenario {scenario_num}: Sensitive Data Harvesting

**Threat Actor Profile:** External attacker or competitor
**Difficulty Level:** Easy
**Potential Impact:** Mass extraction of customer PII and internal credentials

### Attack Steps:
1. **API Discovery** — Attacker identifies `{path}` through reconnaissance
2. **Data Mining** — Sends crafted requests to extract exposed fields: {pii}
3. **Data Aggregation** — Combines harvested data to build complete customer profiles
4. **Monetization** — Sells data on dark web or uses for identity theft / targeted phishing

### Evidence from Scan Data:
- {de.get('details', 'Sensitive data exposed in API responses')}

### Real-World Parallel:
- Facebook's 2021 data leak exposed 533M users' personal data through API scraping

### How to Prevent This:
- Immediately mask or remove all PII from API responses
- Implement field-level access controls
- Add response filtering at the API gateway""")
        scenario_num += 1

    # Scenario: No Input Validation
    iv = posture.get("input_validation", {})
    if iv.get("status") == "fail":
        scenarios.append(f"""## ⚔ Attack Scenario {scenario_num}: Injection Attack

**Threat Actor Profile:** Skilled external attacker
**Difficulty Level:** Moderate to Advanced
**Potential Impact:** Remote code execution, database compromise, full system takeover

### Attack Steps:
1. **Probe** — Attacker sends malformed input to `{path}` to test for validation
2. **Injection** — Crafts SQL injection or command injection payloads through unvalidated fields
3. **Database Access** — Gains direct access to the backend database
4. **Privilege Escalation** — Uses database access to escalate to admin privileges

### Evidence from Scan Data:
- {iv.get('details', 'No input validation configured')}

### How to Prevent This:
- Implement strict input validation with schema enforcement
- Use parameterized queries for all database operations
- Deploy a Web Application Firewall (WAF)""")
        scenario_num += 1

    if not scenarios:
        return (f"## ✅ Attack Simulation: {name}\n\n"
                f"No significant attack vectors were identified for `{path}`. "
                f"The current security posture adequately protects against common attack patterns.\n\n"
                f"**Continue monitoring for:**\n"
                f"- New vulnerability disclosures\n"
                f"- Changes in traffic patterns\n"
                f"- Configuration drift\n\n"
                f"*Simulation generated by Lazarus Local AI Engine*")

    return ("\n\n".join(scenarios) +
            "\n\n---\n*⚠ These are simulated scenarios for educational purposes. "
            "Generated by Lazarus Local AI Engine using actual scan data.*")


# ═══════════════════════════════════════════════════════════════
# 5. AI SECURITY SUMMARY (for Dashboard)
# ═══════════════════════════════════════════════════════════════

def security_summary(all_apis: list, analysis: dict) -> str:
    """
    Generate a brief executive summary of the overall API security posture
    for the dashboard home page.
    """
    _simulated_delay()

    total = len(all_apis)
    shadows = len(analysis.get("shadow_apis", []))
    zombies = len(analysis.get("zombie_apis", []))
    stales = len(analysis.get("stale_apis", []))
    active = total - shadows - zombies - stales

    critical_count = sum(1 for a in all_apis
                         if a.get("security_posture", {}).get("risk_level", "").upper() == "CRITICAL")
    avg_score = sum(a.get("security_posture", {}).get("overall_score", 0)
                    for a in all_apis) / max(total, 1)

    # Find worst API
    worst_api = min(all_apis, key=lambda a: a.get("security_posture", {}).get("overall_score", 100),
                    default=None)
    worst_name = worst_api.get("name", "Unknown") if worst_api else "N/A"
    worst_score = worst_api.get("security_posture", {}).get("overall_score", "N/A") if worst_api else "N/A"

    # Find best API
    best_api = max(all_apis, key=lambda a: a.get("security_posture", {}).get("overall_score", 0),
                   default=None)
    best_name = best_api.get("name", "Unknown") if best_api else "N/A"
    best_score = best_api.get("security_posture", {}).get("overall_score", "N/A") if best_api else "N/A"

    summary = (
        f"Lazarus is monitoring **{total} APIs** across the bank's infrastructure "
        f"(avg security score: **{avg_score:.0f}/100**). "
    )

    if critical_count > 0:
        summary += (
            f"🔴 **{critical_count} API(s) are at CRITICAL risk** — "
            f"the most concerning is **{worst_name}** (score: {worst_score}/100), "
            f"which needs immediate attention. "
        )
    else:
        summary += "No APIs are at critical risk level currently. "

    if shadows > 0:
        summary += f"👻 {shadows} undocumented shadow API(s) detected in live traffic. "

    if zombies > 0:
        summary += f"🧟 {zombies} zombie API(s) still receiving traffic despite being deprecated. "

    summary += (
        f"🟢 **{best_name}** leads with the highest security score ({best_score}/100). "
        f"Recommend prioritizing remediation of critical-risk APIs and investigating shadow endpoints."
    )

    return summary
