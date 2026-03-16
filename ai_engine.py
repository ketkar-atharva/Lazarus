"""
AI Interpretation Layer for Lazarus — Zombie API Discovery & Defence.

Uses Google Gemini (gemini-2.0-flash-lite) to power:
  1. AI Risk Explanation Engine
  2. Natural Language Security Queries
  3. Automated Security Report Generator
  4. Attack Scenario Simulator

Set your API key via environment variable GEMINI_API_KEY or in a .env file.
"""

import os
import json
import time
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
# import google.generativeai as genai
from dotenv import load_dotenv
from google import genai


# Load .env FIRST before anything else
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_ENV_PATH, override=True)

# NOW it's safe to read env vars
_MODEL = "gemini-1.5-flash"
_client = None
_last_api_key = None

API_KEY = os.environ.get("GEMINI_API_KEY", "")

def _get_client():
    global _client, _last_api_key
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not set. Export it as an environment variable or add to .env"
        )

    if _client is None or api_key != _last_api_key:
        _client = genai.Client(api_key=api_key)
        _last_api_key = api_key
    return _client


def _extract_text_from_response(response):
    """Extract a human-readable text string from a Gemini GenerateContentResponse."""
    # Primary path: client.models.generate_content() returns GenerateContentResponse
    # whose .text property concatenates all text parts automatically.
    text = getattr(response, "text", None)
    if text:
        return text

    # Fallback: iterate candidates → content → parts manually
    candidates = getattr(response, "candidates", None)
    if candidates:
        parts = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if content:
                for part in getattr(content, "parts", []):
                    part_text = getattr(part, "text", None)
                    if part_text:
                        parts.append(part_text)
        if parts:
            return "\n\n".join(parts)

    # Last-resort: str representation
    return str(response)


def _call_with_retry(prompt, max_retries=3):
    """Call Gemini with automatic retry on quota/rate-limit errors."""
    for attempt in range(max_retries):
        try:
            client = _get_client()
            response = client.models.generate_content(model=_MODEL, contents=prompt)
            return _extract_text_from_response(response)
        except Exception as e:
            err_str = str(e).lower()
            if any(kw in err_str for kw in ["quota", "rate", "429", "resource_exhausted"]):
                if attempt < max_retries - 1:
                    wait = (2 ** attempt) * 2  # 2s, 4s, 8s
                    time.sleep(wait)
                    continue
                raise RuntimeError(
                    "The AI service is temporarily busy (rate limit reached). "
                    "Please wait a minute and try again."
                )
            raise


def _safe_json(data):
    """Convert data to JSON string, handling non-serializable types."""
    def default(o):
        return str(o)
    return json.dumps(data, indent=2, default=default)


# ═══════════════════════════════════════════════════════════════
# 1. AI RISK EXPLANATION ENGINE
# ═══════════════════════════════════════════════════════════════

def explain_risk(api_detail: dict) -> str:
    """
    Translate complex API security findings into clear, business-friendly
    risk explanations for non-technical banking employees.
    """


    system_prompt = """You are a senior cybersecurity advisor working inside a commercial bank. 
Your audience is non-technical banking employees — branch managers, compliance officers, 
and operations staff who do NOT understand technical jargon.

Your job is to take raw API security scan data and explain:
1. **What is this API?** — One sentence, plain English.
2. **What's wrong?** — Explain each security finding like you're talking to a colleague over coffee. No jargon.
3. **Why should I care? (Business Impact)** — Translate each risk into real bank consequences: 
   financial loss, regulatory fines, customer data breach, reputation damage.
4. **Risk Level** — Give a simple traffic-light rating: 🔴 Critical, 🟡 Warning, 🟢 Safe.
5. **What should we do?** — Simple, actionable next steps a non-technical person can understand.

RULES:
- Never use words like "endpoint", "vector", "payload", "injection", "TLS", "OAuth" without explaining them.
- Use analogies from banking (e.g., "This is like leaving the vault door unlocked overnight").
- Keep it concise — aim for 200-400 words.
- Use markdown formatting with headers, bullet points, and bold text.
- Always start with a one-line summary."""

    prompt = f"""{system_prompt}

Here is the raw API security scan data to explain:

```json
{_safe_json(api_detail)}
```

Generate the risk explanation now."""

    return _call_with_retry(prompt)


# ═══════════════════════════════════════════════════════════════
# 2. NATURAL LANGUAGE SECURITY QUERIES
# ═══════════════════════════════════════════════════════════════

def query_security(question: str, all_apis: list, analysis: dict) -> str:
    """
    Answer natural-language security questions by searching the
    security findings database using Gemini as the reasoning engine.
    """


    system_prompt = """You are the AI assistant for "Lazarus", a bank's API security platform.
The user is a non-technical banking employee asking questions about their API security posture.

You have access to the complete API security database provided below. Use ONLY this data to answer.

RULES:
- Answer in clear, non-technical language suitable for banking staff.
- Always reference specific API names/paths when relevant.
- If the data doesn't contain enough information to answer, say so honestly.
- Use markdown formatting with headers, bullet points, and bold text for readability.
- Keep answers focused and concise (150-300 words).
- If the user asks about something outside the security data, politely redirect to security topics.
- Include specific numbers, scores, and details from the data to support your answer.
- End with a brief recommendation or next step when applicable."""

    prompt = f"""{system_prompt}

═══ COMPLETE API SECURITY DATABASE ═══

API Details & Security Postures:
```json
{_safe_json(all_apis)}
```

Threat Analysis Summary:
```json
{_safe_json(analysis)}
```

═══ USER QUESTION ═══
{question}

Answer the question using only the data above."""

    return _call_with_retry(prompt)


# ═══════════════════════════════════════════════════════════════
# 3. AUTOMATED SECURITY REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_report(api_detail: dict) -> str:
    """
    Generate a comprehensive security & compliance report for an API,
    enriched with AI risk assessments and recommendations.
    """


    system_prompt = """You are a cybersecurity compliance officer at a major Indian commercial bank 
regulated by RBI (Reserve Bank of India) and subject to PCI-DSS v4.0 requirements.

Generate a formal, comprehensive API Security & Compliance Report. The report should be 
professional enough to present to:
- The CISO (Chief Information Security Officer)
- The bank's compliance department
- External RBI auditors

REPORT STRUCTURE:
# 🔒 API Security & Compliance Report

## Executive Summary
One paragraph summarizing the API, its risk level, and key findings.

## API Overview
Table with: Name, Path, Method, Version, Owner, Status, Last Updated.

## Security Assessment
For each security dimension (Authentication, Encryption, Rate Limiting, Data Exposure, Input Validation):
- Current status (Pass/Warning/Fail)
- Finding details
- Risk rating
- Compliance impact

## Risk Analysis
- Overall risk score and level
- Business impact assessment
- Potential financial exposure estimate
- Regulatory non-compliance risks

## Compliance Mapping
Map findings to specific regulatory requirements:
- RBI IT Framework 2023
- PCI-DSS v4.0 requirements
- Data Protection guidelines

## Remediation Roadmap
Prioritized list of actions with timeline suggestions:
- Immediate (within 24 hours)
- Short-term (within 1 week)
- Medium-term (within 1 month)

## Conclusion
Final assessment and sign-off recommendation.

RULES:
- Use professional, formal language suitable for regulatory documentation.
- Include specific data points and scores from the scan.
- Use markdown formatting with tables, headers, and structured lists.
- Aim for 500-800 words."""

    prompt = f"""{system_prompt}

Here is the raw API security scan data:

```json
{_safe_json(api_detail)}
```

Generate the complete report now."""

    return _call_with_retry(prompt)


# ═══════════════════════════════════════════════════════════════
# 4. ATTACK SCENARIO SIMULATOR
# ═══════════════════════════════════════════════════════════════

def simulate_attack(api_detail: dict) -> str:
    """
    Generate hypothetical attack scenarios showing how a threat actor
    could exploit the discovered API vulnerabilities step-by-step.
    """


    system_prompt = """You are a red-team security specialist conducting a simulated threat assessment 
for a bank's API security team. Your job is to show — in educational terms — how real-world 
attackers could exploit the vulnerabilities found in the scan data.

Generate 2-3 realistic attack scenarios based on the ACTUAL vulnerabilities found.

FORMAT FOR EACH SCENARIO:
## ⚔ Attack Scenario [N]: [Attack Name]

**Threat Actor Profile:** [Who would do this — e.g., external hacker, insider threat, script kiddie]
**Difficulty Level:** [Easy / Moderate / Advanced]
**Potential Impact:** [What they could achieve]

### Attack Steps:
1. **[Step Name]** — [Detailed description of what the attacker does]
2. **[Step Name]** — [Next step in the attack chain]
3. ... continue until objective is achieved

### Evidence from Scan Data:
- [Quote specific findings that make this attack possible]

### Real-World Parallel:
- [Reference a similar real attack or breach, if applicable]

### How to Prevent This:
- [Specific countermeasures]

RULES:
- Only generate scenarios based on ACTUAL vulnerabilities found in the scan data. Do NOT invent vulnerabilities.
- Explain in language understandable to non-technical banking staff.
- Use analogies from physical security when helpful (e.g., "This is like finding a back door 
  with no lock — anyone who finds it can walk in").
- Be educational, not instructional — show what COULD happen, not how to do it.
- Use markdown formatting with clear headers and numbered steps.
- Aim for 400-600 words total across all scenarios."""

    prompt = f"""{system_prompt}

Here is the API security scan data to analyze:

```json
{_safe_json(api_detail)}
```

Generate the attack scenarios now."""

    return _call_with_retry(prompt)


# ═══════════════════════════════════════════════════════════════
# 5. AI SECURITY SUMMARY (for Dashboard)
# ═══════════════════════════════════════════════════════════════

def security_summary(all_apis: list, analysis: dict) -> str:
    """
    Generate a brief executive summary of the overall API security posture
    for the dashboard home page.
    """


    system_prompt = """You are the AI security advisor for a bank's API security platform called Lazarus.
Generate a brief executive summary (3-5 sentences) of the bank's overall API security posture 
based on the scan data. Written for a non-technical banking manager.

Include:
- Total number of APIs and their status breakdown
- The most critical risk that needs attention RIGHT NOW
- One positive highlight (something that's working well)
- A one-line recommendation

Keep it warm and professional. Use emoji sparingly. Format in markdown."""

    prompt = f"""{system_prompt}

API Security Data:
```json
{_safe_json(all_apis)}
```

Threat Analysis:
```json
{_safe_json(analysis)}
```

Generate the summary now."""

    return _call_with_retry(prompt)
