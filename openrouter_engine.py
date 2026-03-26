"""
OpenRouter AI Engine for Lazarus — Zombie API Discovery & Defence.

Provides a real LLM-powered chat experience using OpenRouter's API (Qwen model).
All security context (API data, analysis results) is injected into the system
prompt so the model can answer questions intelligently about your actual data.

Configuration (add these to your .env file):
    OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
    OPENROUTER_MODEL=qwen/qwen3-235b-a22b-2507

Free Qwen models available on OpenRouter:
    - qwen/qwen3-235b-a22b:free   (most capable, free tier)
    - qwen/qwen3-30b-a3b:free
    - qwen/qwq-32b:free
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# ── Force load .env from multiple possible locations ─────────────────────────

def load_env_file():
    """Try to load .env from multiple locations and return success status."""
    possible_paths = [
        Path.cwd() / ".env",  # Current working directory
        Path(__file__).parent / ".env",  # Same directory as this script
        Path(__file__).parent.parent / ".env",  # Parent directory
        Path("C:/UBI/.env"),  # Your specific path from error message
    ]
    
    for env_path in possible_paths:
        if env_path.exists():
            print(f"✓ Found .env file at: {env_path}", file=sys.stderr)
            load_dotenv(env_path, override=True)
            return True
    
    print(f"✗ No .env file found in any of these locations:", file=sys.stderr)
    for p in possible_paths:
        print(f"  - {p}", file=sys.stderr)
    return False

# Load environment variables
load_env_file()

# ── Configuration ─────────────────────────────────────────────────────────────

OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"

# Load from environment variables with debugging
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-235b-a22b:free").strip()

# Debug output (remove after testing)
print(f"DEBUG: API Key loaded: {'Yes' if OPENROUTER_API_KEY else 'No'}", file=sys.stderr)
print(f"DEBUG: API Key length: {len(OPENROUTER_API_KEY)}", file=sys.stderr)
print(f"DEBUG: Model: {OPENROUTER_MODEL}", file=sys.stderr)

# How many past messages to send for multi-turn context (keeps costs low)
MAX_HISTORY_MESSAGES: int = 10


# ── System Prompt Builder ─────────────────────────────────────────────────────

def _build_system_prompt(api_data: list, analysis: dict) -> str:
    """
    Construct a rich system prompt that injects live API security data
    so the model can answer domain-specific questions accurately.
    """
    total = len(api_data)
    shadows = len(analysis.get("shadow_apis", []))
    zombies = len(analysis.get("zombie_apis", []))
    stales = len(analysis.get("stale_apis", []))

    critical_apis = [
        a for a in api_data
        if a.get("security_posture", {}).get("risk_level", "").upper() == "CRITICAL"
    ]
    avg_score = (
        sum(a.get("security_posture", {}).get("overall_score", 0) for a in api_data)
        / max(total, 1)
    )

    # Compact API listing for context injection
    api_lines = []
    for api in api_data[:20]:  # cap to avoid huge prompts
        posture = api.get("security_posture", {})
        api_lines.append(
            f"  - {api.get('name', 'Unknown')} ({api.get('path', '')}) | "
            f"Score: {posture.get('overall_score', 'N/A')}/100 | "
            f"Risk: {posture.get('risk_level', 'N/A')} | "
            f"Auth: {posture.get('authentication', {}).get('status', 'N/A')} | "
            f"Enc: {posture.get('encryption', {}).get('status', 'N/A')}"
        )
    api_summary = "\n".join(api_lines) if api_lines else "  No API data available."

    critical_lines = []
    for api in critical_apis:
        posture = api.get("security_posture", {})
        issues = []
        for check in ["authentication", "encryption", "rate_limiting", "data_exposure", "input_validation"]:
            if posture.get(check, {}).get("status") == "fail":
                issues.append(check.replace("_", " "))
        critical_lines.append(
            f"  - {api.get('name')} ({api.get('path')}): Failed — {', '.join(issues)}"
        )
    critical_summary = "\n".join(critical_lines) if critical_lines else "  None"

    shadow_paths = analysis.get("shadow_apis", [])
    zombie_paths = analysis.get("zombie_apis", [])

    return f"""You are Lazarus AI, an expert API security assistant embedded inside the Lazarus — Zombie API Discovery & Defence platform. You work with a bank's security team to help them understand API risks, compliance issues, and remediation steps.

You are friendly, professional, and explain technical concepts in plain English that non-technical banking staff can understand. Use real-world analogies when helpful. Use markdown formatting in your responses.

== LIVE SECURITY DATA (as of this session) ==

Platform Overview:
  Total APIs monitored: {total}
  Average security score: {avg_score:.0f}/100
  Critical-risk APIs: {len(critical_apis)}
  Shadow (undocumented) APIs: {shadows}
  Zombie (deprecated but active) APIs: {zombies}
  Stale (zero-traffic) APIs: {stales}

All APIs:
{api_summary}

Critical Risk APIs (need immediate attention):
{critical_summary}

Shadow API paths: {', '.join(shadow_paths) if shadow_paths else 'None'}
Zombie API paths: {', '.join(zombie_paths) if zombie_paths else 'None'}

== YOUR ROLE ==
- Answer security questions using the LIVE DATA above
- Explain risks in plain English (non-technical banking staff are your audience)
- Recommend concrete, actionable remediation steps
- Reference RBI IT Framework and PCI-DSS v4.0 standards when relevant
- Keep responses concise but complete — use bullet points and headers
- If asked about a specific API not in the data, say so clearly
- Never make up security scores or findings — only use the data provided above

If you don't have enough data to answer something completely, say so and suggest what the user could check in the Lazarus dashboard."""


# ── Main Chat Function ────────────────────────────────────────────────────────

def chat_with_openrouter(
    question: str,
    api_data: list,
    analysis: dict,
    history: list | None = None,
) -> str:
    """
    Send a message to OpenRouter (Qwen) and return the assistant's reply.

    Args:
        question:   The user's current message.
        api_data:   List of full API detail objects (from _gather_all_api_details).
        analysis:   The analysis dict (zombie_apis, shadow_apis, stale_apis).
        history:    Optional list of past messages in OpenAI format:
                    [{"role": "user"|"assistant", "content": "..."}]

    Returns:
        The assistant's reply string, or an error message if the call fails.
    """
    # ── Guard: API key with better debugging ──
    if not OPENROUTER_API_KEY:
        # Get current working directory for better error message
        cwd = Path.cwd()
        script_dir = Path(__file__).parent
        
        return (
            "⚠ **OpenRouter API key not configured.**\n\n"
            f"**Current working directory:** `{cwd}`\n"
            f"**Script directory:** `{script_dir}`\n\n"
            "**Please ensure your `.env` file exists in one of these locations and contains:**\n"
            "```\n"
            "OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx\n"
            "OPENROUTER_MODEL=qwen/qwen3-235b-a22b:free\n"
            "```\n\n"
            "**Important:** No quotes around the values, no spaces around the `=` sign.\n\n"
            "Get your free key at https://openrouter.ai/keys"
        )

    # ── Build messages list ──
    system_prompt = _build_system_prompt(api_data, analysis)
    messages = [{"role": "system", "content": system_prompt}]

    # Append trimmed conversation history
    if history:
        trimmed = history[-(MAX_HISTORY_MESSAGES - 1):]  # keep within token budget
        for msg in trimmed:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    # Append current question
    messages.append({"role": "user", "content": question})

    # ── Call OpenRouter ──
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",   # OpenRouter requires a referer
        "X-Title": "Lazarus API Security Platform",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    try:
        response = requests.post(
            OPENROUTER_BASE_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        # Extract reply
        reply = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if not reply:
            return "⚠ The AI returned an empty response. Please try again."
        return reply

    except requests.exceptions.Timeout:
        return (
            "⚠ **Request timed out.** OpenRouter took too long to respond.\n\n"
            "Please try again in a moment."
        )
    except requests.exceptions.ConnectionError:
        return (
            "⚠ **Connection error.** Could not reach OpenRouter.\n\n"
            "Please check your internet connection and try again."
        )
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "?"
        try:
            err_detail = e.response.json().get("error", {}).get("message", str(e))
        except Exception:
            err_detail = str(e)

        if status_code == 401:
            return (
                "⚠ **Invalid API key (401 Unauthorized).**\n\n"
                "Please double-check your `OPENROUTER_API_KEY` in `.env`.\n"
                "Make sure there are no extra spaces or quotes around the key."
            )
        elif status_code == 429:
            return (
                "⚠ **Rate limit hit (429 Too Many Requests).**\n\n"
                "You've exceeded the free-tier limit. Wait a moment and try again, "
                "or upgrade your OpenRouter plan."
            )
        elif status_code == 402:
            return (
                "⚠ **Insufficient credits (402).**\n\n"
                "Your OpenRouter account has run out of credits. "
                "Add credits at https://openrouter.ai/credits or use a `:free` model."
            )
        return (
            f"⚠ **OpenRouter API error ({status_code}):** {err_detail}\n\n"
            "Please check your configuration and try again."
        )
    except Exception as e:
        return f"⚠ **Unexpected error:** {str(e)}"


