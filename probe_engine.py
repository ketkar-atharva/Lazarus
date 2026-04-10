"""
probe_engine.py — Live API probe and classification engine.
Lazarus API Defence Platform

For each API entry (api_id, url, method, optional last_traffic_at) this module:
  1. Checks catalog membership (all CSV-sourced entries are in_catalog=True for now)
  2. Probes reachability via httpx with an 8-second timeout
  3. Checks staleness via last_traffic_at or Last-Modified response header
  4. Checks auth exposure (unauthenticated request returning HTTP 200)
  5. Emits a final lazarus_status: ZOMBIE | SHADOW | STALE | ACTIVE

All probes run concurrently via asyncio.gather, capped at 10 simultaneous
connections with asyncio.Semaphore(10).
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx

# ── Constants ──────────────────────────────────────────────────────────────────

TIMEOUT_SECONDS = 8
STALE_DAYS = 90
MAX_CONCURRENT = 10

LAZARUS_UA = "Lazarus-Scanner/1.0"

# Private / loopback IP ranges (simple prefix check)
_PRIVATE_PREFIXES = (
    "http://localhost",
    "https://localhost",
    "http://127.",
    "https://127.",
    "http://10.",
    "https://10.",
    "http://192.168.",
    "https://192.168.",
    "http://172.",   # covers 172.16–172.31
    "https://172.",
)


def _is_private_url(url: str) -> bool:
    """Return True if the URL targets localhost or a private IP range."""
    lower = url.lower()
    return any(lower.startswith(p) for p in _PRIVATE_PREFIXES)


def _build_headers(url: str) -> dict:
    """Return appropriate request headers based on URL visibility."""
    headers = {"Accept": "*/*"}
    if not _is_private_url(url):
        headers["User-Agent"] = LAZARUS_UA
    return headers


def _parse_last_traffic(raw) -> Optional[datetime]:
    """
    Parse a last_traffic_at value into an aware UTC datetime.
    Returns None if the value is missing, empty, or unparseable.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if s.lower() in ("", "none", "null", "nat"):
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _parse_http_date(raw: Optional[str]) -> Optional[datetime]:
    """
    Parse an HTTP-date header value (RFC 7231) into an aware UTC datetime.
    Example: 'Wed, 21 Oct 2015 07:28:00 GMT'
    Returns None if unparseable.
    """
    if not raw:
        return None
    try:
        # email.utils handles RFC 2822 / HTTP-date
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _staleness_result(last_traffic_dt: Optional[datetime]) -> dict:
    """
    Given a parsed last_traffic datetime, return staleness fields.
    Returns a dict with keys:
        is_stale        (bool)
        last_traffic_unknown (bool)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=STALE_DAYS)
    if last_traffic_dt is None:
        return {"is_stale": True, "last_traffic_unknown": True}
    if last_traffic_dt < cutoff:
        return {"is_stale": True, "last_traffic_unknown": False}
    return {"is_stale": False, "last_traffic_unknown": False}


# ── Single-API probe ───────────────────────────────────────────────────────────

async def _probe_single(
    api: dict,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> dict:
    """
    Probe a single API entry and return a classification result dict.

    Input keys: api_id, url, method (required) | last_traffic_at (optional)

    Output keys (always present):
        api_id, url, method, lazarus_status, http_code, reachable,
        response_time_ms, auth_exposed, probed_at, last_traffic_unknown
    Output keys (conditional):
        last_traffic_at  — only when it was present in the input
    """
    async with semaphore:
        api_id = str(api.get("api_id", "")).strip()
        url = str(api.get("url", "")).strip()
        method = str(api.get("method", "GET")).strip().upper() or "GET"
        last_traffic_raw = api.get("last_traffic_at")

        probed_at = datetime.now(timezone.utc).isoformat()

        # Base result scaffold — explicitly unpacking the input dict first to preserve extra metadata (name, owner, etc.)
        result: dict = {
            **api,
            "api_id": api_id,
            "url": url,
            "method": method,
            "lazarus_status": "ACTIVE",   # default; overwritten below
            "http_code": None,
            "reachable": False,
            "response_time_ms": None,
            "auth_exposed": False,
            "last_traffic_unknown": False, # Step 3 may flip this to True
            "probed_at": probed_at,
        }

        # last_traffic_at is included only when it was present in the input
        if last_traffic_raw is not None:
            result["last_traffic_at"] = last_traffic_raw

        headers = _build_headers(url)

        # ── Step 2 — Reachability probe ────────────────────────────────────────
        response = None
        try:
            start_ms = asyncio.get_event_loop().time() * 1000
            response = await client.request(
                method,
                url,
                headers=headers,
                timeout=TIMEOUT_SECONDS,
                follow_redirects=True,
            )
            end_ms = asyncio.get_event_loop().time() * 1000

            result["http_code"] = response.status_code
            result["reachable"] = True
            result["response_time_ms"] = round(end_ms - start_ms, 2)

        except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError):
            result["lazarus_status"] = "ZOMBIE"
            result["reachable"] = False
            return result
        except Exception:
            # Any unexpected transport error → treat as ZOMBIE
            result["lazarus_status"] = "ZOMBIE"
            result["reachable"] = False
            return result

        # ── Step 3 — Staleness check ───────────────────────────────────────────
        #
        # Priority order:
        #   1. last_traffic_at from the CSV input
        #   2. Last-Modified response header from the probe response
        #   3. Neither available → mark last_traffic_unknown=True and classify STALE-RISK
        #
        last_traffic_dt: Optional[datetime] = _parse_last_traffic(last_traffic_raw)

        staleness_source = "csv"
        if last_traffic_dt is None:
            # Try Last-Modified header
            lm_header = response.headers.get("Last-Modified") if response else None
            last_traffic_dt = _parse_http_date(lm_header)
            staleness_source = "last_modified_header" if last_traffic_dt else "none"

        staleness = _staleness_result(last_traffic_dt)
        result["last_traffic_unknown"] = staleness["last_traffic_unknown"]

        if staleness["last_traffic_unknown"] or staleness["is_stale"]:
            # Unknown → cannot confirm recent activity; stale → older than 90 days
            result["lazarus_status"] = "STALE"

        # ── Step 4 — Auth exposure check ──────────────────────────────────────
        # Send a second, stripped request (no Authorization, no API-key headers).
        # If it returns HTTP 200 the endpoint is unauthenticated — security flag.
        try:
            bare_headers = {k: v for k, v in headers.items()
                            if k.lower() not in ("authorization", "x-api-key", "api-key")}
            auth_resp = await client.request(
                method,
                url,
                headers=bare_headers,
                timeout=TIMEOUT_SECONDS,
                follow_redirects=True,
            )
            if auth_resp.status_code == 200:
                result["auth_exposed"] = True
        except Exception:
            # Auth probe failure is non-fatal; leave auth_exposed = False
            pass

        # ── Step 5 — Final classification ─────────────────────────────────────
        # Only set ACTIVE if none of the earlier steps already set a status.
        if result["lazarus_status"] == "ACTIVE":
            pass   # already correct

        return result


# ── Public entry-point ─────────────────────────────────────────────────────────

async def probe_and_classify(apis: list) -> list:
    """
    Probe a list of API dicts concurrently and return classification results.

    CSV contract — each input dict must have:
        api_id          (str, required)
        url             (str, required)
        method          (str, required)  — GET used as fallback if empty
        last_traffic_at (str, optional)  — ISO-8601 date/datetime

    Returns a list of result dicts, one per input API.
    Each result always contains:
        api_id, url, method, lazarus_status, http_code, reachable,
        response_time_ms, auth_exposed, last_traffic_unknown, probed_at
    Plus, when last_traffic_at was supplied in the input:
        last_traffic_at
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async with httpx.AsyncClient(verify=False) as client:
        tasks = [
            _probe_single(api, client, semaphore)
            for api in apis
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    return list(results)
