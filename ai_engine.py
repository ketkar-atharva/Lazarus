"""
AI Interpretation Layer for Lazarus — Zombie API Discovery & Defence.

Optimized version with MINIMAL token usage to avoid quota limits.
Uses compact text summaries instead of full JSON dumps.
"""

import os
import json
import time
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from dotenv import load_dotenv
from google import genai

# ── Load .env before reading any env vars ──────────────────────────────────────
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_ENV_PATH, override=True)

# ── EXPOSE API_KEY at module level for server.py ───────────────────────────────
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# ── Use gemini-1.5-flash for better stability and quota ────────────────────────
_MODEL = "gemini-1.5-flash"

_client = None
_last_api_key = None


# ── Lazy client factory ────────────────────────────────────────────────────────
def _get_client():
    global _client, _last_api_key
    api_key = os.environ.get("GEMINI_API_KEY", API_KEY).strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not set. Export it as an environment variable or add it to .env"
        )
    if _client is None or api_key != _last_api_key:
        _client = genai.Client(api_key=api_key)
        _last_api_key = api_key
    return _client


# ── Response text extractor ────────────────────────────────────────────────────
def _extract_text_from_response(response) -> str:
    """Safely pull plain text out of any Gemini response shape."""
    text = getattr(response, "text", None)
    if text:
        return text

    for candidate in getattr(response, "candidates", []):
        content = getattr(candidate, "content", None)
        if content:
            parts = [
                p.text for p in getattr(content, "parts", [])
                if getattr(p, "text", None)
            ]
            if parts:
                return "\n\n".join(parts)

    return str(response)


# ── Token estimation helper ────────────────────────────────────────────────────
def _estimate_tokens(text: str) -> int:
    """Rough token estimate (1 token ≈ 4 characters)"""
    return len(text) // 4


# ── Retry wrapper with token limit check ───────────────────────────────────────
def _call_with_retry(prompt: str, max_retries: int = 3) -> str:
    """
    Call Gemini with exponential back-off on quota / rate-limit errors.
    Includes token limit safety check.
    """
    # Check token count before sending
    estimated_tokens = _estimate_tokens(prompt)
    print(f"🔍 Sending ~{estimated_tokens:,} tokens to Gemini")
    
    if estimated_tokens > 25000:
        raise ValueError(
            f"Prompt too large ({estimated_tokens:,} tokens). "
            f"Maximum is 25,000 tokens. Reduce the data being sent."
        )
    
    for attempt in range(max_retries):
        try:
            client = _get_client()
            response = client.models.generate_content(
                model=_MODEL,
                contents=prompt,
            )
            return _extract_text_from_response(response)

        except Exception as exc:
            err = str(exc).lower()
            is_rate_limit = any(k in err for k in ("quota", "rate", "429", "resource_exhausted"))

            if is_rate_limit and attempt < max_retries - 1:
                wait = (2 ** attempt) * 2
                print(f"⏳ Rate limited. Waiting {wait}s before retry {attempt + 2}/{max_retries}...")
                time.sleep(wait)
                continue

            if is_rate_limit:
                raise RuntimeError(
                    "The AI service is temporarily busy (rate limit reached). "
                    "Please wait a minute and try again."
                ) from exc

            raise


# ── Helper: Create compact API summary ─────────────────────────────────────────
def _create_compact_api_summary(api_detail: dict) -> str:
    """Convert full API detail to compact text summary (saves 90% tokens)"""
    posture = api_detail.get("security_posture", {})
    findings = posture.get("findings", [])
    
    critical_findings = [f for f in findings if f.get("severity") == "critical"]
    high_findings = [f for f in findings if f.get("severity") == "high"]
    
    summary = f"""
API: {api_detail.get('path', 'Unknown')}
Method: {api_detail.get('method', 'Unknown')}
Status: {api_detail.get('status', 'Unknown')}
Overall Security Score: {posture.get('overall_score', 'N/A')}/100

Security Findings:
- Critical Issues: {len(critical_findings)}
- High Risk Issues: {len(high_findings)}
- Total Findings: {len(findings)}

Authentication: {posture.get('authentication', {}).get('status', 'Unknown')}
Encryption: {posture.get('encryption', {}).get('status', 'Unknown')}
Rate Limiting: {posture.get('rate_limiting', {}).get('status', 'Unknown')}

Top Issues:
"""
    
    # Add top 3 most critical findings
    top_findings = sorted(findings, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("severity", "low"), 4))[:3]
    for i, finding in enumerate(top_findings, 1):
        summary += f"{i}. [{finding.get('severity', 'Unknown').upper()}] {finding.get('finding', 'No details')}\n"
    
    return summary.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. AI RISK EXPLANATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def explain_risk(api_detail: dict) -> str:
    """
    Translate complex API security findings into clear, business-friendly
    risk explanations for non-technical banking employees.
    """
    # Create compact summary instead of full JSON
    api_summary = _create_compact_api_summary(api_detail)
    
    prompt = f"""You are a senior cybersecurity advisor at a commercial bank.
Explain these API security findings to non-technical banking employees in simple terms.

{api_summary}

Provide:
1. What is this API? (1 sentence)
2. What's wrong? (plain English, no jargon)
3. Why should we care? (business impact: money, reputation, compliance)
4. Risk Level: 🔴 Critical / 🟡 Warning / 🟢 Safe
5. What should we do? (simple next steps)

Keep it under 300 words. Use banking analogies. Format in markdown."""

    return _call_with_retry(prompt)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. NATURAL LANGUAGE SECURITY QUERIES
# ═══════════════════════════════════════════════════════════════════════════════

def query_security(question: str, all_apis: list, analysis: dict) -> str:
    """
    Answer natural-language security questions by reasoning over the
    API security data.
    """
    # Create compact summary of ALL APIs
    total_apis = len(all_apis)
    critical_apis = [a for a in all_apis if a.get("security_posture", {}).get("overall_score", 100) < 30]
    high_risk_apis = [a for a in all_apis if 30 <= a.get("security_posture", {}).get("overall_score", 100) < 60]
    
    shadow_count = len(analysis.get("shadow_apis", []))
    zombie_count = len(analysis.get("zombie_apis", []))
    
    # Build compact text summary
    data_summary = f"""
SECURITY OVERVIEW:
- Total APIs: {total_apis}
- Critical Risk (score < 30): {len(critical_apis)} APIs
- High Risk (score 30-60): {len(high_risk_apis)} APIs
- Shadow APIs (undocumented): {shadow_count}
- Zombie APIs (deprecated but active): {zombie_count}

CRITICAL APIS:"""
    
    for api in critical_apis[:5]:  # Only top 5
        posture = api.get("security_posture", {})
        data_summary += f"""
  • {api.get('path')} - Score: {posture.get('overall_score')}/100
    Issues: {len([f for f in posture.get('findings', []) if f.get('severity') == 'critical'])} critical"""
    
    data_summary += f"""

SHADOW APIS:"""
    for shadow in analysis.get("shadow_apis", [])[:3]:  # Only top 3
        data_summary += f"\n  • {shadow.get('path')} ({shadow.get('method')})"
    
    prompt = f"""You are the AI assistant for a bank's API security platform.
Answer this question using ONLY the data below.

{data_summary}

QUESTION: {question}

Answer in clear, non-technical language for banking staff. 
Include specific API names/paths and numbers.
Keep it under 250 words. Format in markdown."""

    return _call_with_retry(prompt)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. AUTOMATED SECURITY REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_report(api_detail: dict) -> str:
    """
    Generate a comprehensive security & compliance report for an API.
    """
    api_summary = _create_compact_api_summary(api_detail)
    
    prompt = f"""You are a cybersecurity compliance officer at a major Indian bank regulated by RBI and PCI-DSS.

Generate a formal API Security & Compliance Report for:

{api_summary}

Include:
# 🔒 API Security & Compliance Report

## Executive Summary
One paragraph with risk level and key findings.

## Security Assessment
For each dimension (Authentication, Encryption, Rate Limiting):
- Status and findings
- Risk rating
- Compliance impact

## Risk Analysis
- Overall score and level
- Business impact
- Regulatory risks (RBI IT Framework, PCI-DSS v4.0)

## Remediation Roadmap
- Immediate (24 hours)
- Short-term (1 week)
- Medium-term (1 month)

## Conclusion
Final assessment and recommendation.

Professional tone suitable for CISO and auditors. 500-700 words. Use markdown."""

    return _call_with_retry(prompt)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ATTACK SCENARIO SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════════

def simulate_attack(api_detail: dict) -> str:
    """
    Generate hypothetical attack scenarios showing how threat actors
    could exploit the discovered vulnerabilities.
    """
    api_summary = _create_compact_api_summary(api_detail)
    
    prompt = f"""You are a red-team security specialist conducting threat assessment for a bank.

Generate 2 realistic attack scenarios based on ACTUAL vulnerabilities found:

{api_summary}

For each scenario include:
## ⚔ Attack Scenario [N]: [Attack Name]
**Threat Actor:** [Type]
**Difficulty:** [Easy/Moderate/Advanced]
**Impact:** [What they achieve]

### Attack Steps:
1. [Step] — [Description]
2. [Step] — [Description]
(continue until objective achieved)

### Evidence from Scan:
- [Specific findings that enable this]

### Prevention:
- [Specific countermeasures]

Educational tone for banking staff. Use banking security analogies.
400-600 words total. Markdown format."""

    return _call_with_retry(prompt)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. AI SECURITY SUMMARY (Dashboard)
# ═══════════════════════════════════════════════════════════════════════════════

def security_summary(all_apis: list, analysis: dict) -> str:
    """
    Generate a brief executive summary of overall API security posture
    for the dashboard home page.
    """
    # Ultra-compact summary
    total_apis = len(all_apis)
    critical_count = len([a for a in all_apis if a.get("security_posture", {}).get("overall_score", 100) < 30])
    high_count = len([a for a in all_apis if 30 <= a.get("security_posture", {}).get("overall_score", 100) < 60])
    shadow_count = len(analysis.get("shadow_apis", []))
    zombie_count = len(analysis.get("zombie_apis", []))
    
    # Get the worst API
    worst_api = None
    if all_apis:
        worst_api = min(all_apis, key=lambda x: x.get("security_posture", {}).get("overall_score", 100))
    
    data_summary = f"""
Total APIs: {total_apis}
Critical Risk APIs: {critical_count}
High Risk APIs: {high_count}
Shadow APIs: {shadow_count}
Zombie APIs: {zombie_count}

Worst API: {worst_api.get('path') if worst_api else 'N/A'} (Score: {worst_api.get('security_posture', {}).get('overall_score') if worst_api else 'N/A'}/100)
"""
    
    prompt = f"""You are the AI security advisor for a bank's API security platform called Lazarus.

Generate a brief executive summary (3-5 sentences) for a banking manager:

{data_summary}

Include:
- Total APIs and status breakdown
- Most critical risk needing attention NOW
- One positive highlight
- One-line recommendation

Warm, professional tone. Use markdown."""

    return _call_with_retry(prompt)