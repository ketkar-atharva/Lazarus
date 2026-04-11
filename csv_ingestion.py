"""
csv_ingestion.py — CSV upload, classification, risk scoring, and catalog routes.
Lazarus API Defence Platform
"""

import io
import csv as csv_module
from datetime import datetime, timezone, timedelta
from typing import Optional, Literal

from pydantic import BaseModel, Field, HttpUrl, ValidationError

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from fastapi.responses import StreamingResponse

import database as db
from probe_engine import probe_and_classify

router = APIRouter(prefix="/catalog", tags=["API Catalog"])

class APIRow(BaseModel):
    api_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    url: HttpUrl
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
    last_traffic_at: Optional[datetime] = None

# ── Required CSV columns (full inventory upload) ──
REQUIRED_COLUMNS = {
    "api_id", "name", "path", "method", "status",
    "is_documented", "traffic_30d", "last_traffic_at",
    "auth_type", "tls_version", "pii_exposure", "has_rate_limit",
}

# ── Required CSV columns (live-probe upload) ──
# Only api_id, url, and method are mandatory; last_traffic_at is optional.
PROBE_REQUIRED_COLUMNS = {"api_id", "url", "method"}

# ── Sample CSV template columns (probe format) ──
SAMPLE_COLUMNS = ["api_id", "url", "method", "last_traffic_at"]


def _to_bool(val) -> bool:
    """Coerce various truthy CSV representations to bool."""
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("true", "1", "yes")


def _to_int(val, default=0) -> int:
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return default


def _classify(row: dict) -> str:
    """
    Determine lazarus_status based on API fields.
    zombie  → status == "deprecated" AND traffic_30d > 0
    shadow  → is_documented == false AND traffic_30d > 0
    stale   → traffic_30d == 0 AND last_traffic_at older than 90 days (or never)
    active  → everything else that is documented and has traffic
    """
    status = str(row.get("status", "")).strip().lower()
    is_documented = _to_bool(row.get("is_documented", True))
    traffic = _to_int(row.get("traffic_30d", 0))
    last_traffic_at_raw = row.get("last_traffic_at", "")

    if status == "deprecated" and traffic > 0:
        return "zombie"

    if not is_documented and traffic > 0:
        return "shadow"

    if traffic == 0:
        if not last_traffic_at_raw or str(last_traffic_at_raw).strip().lower() in ("", "none", "null", "nat"):
            return "stale"
        try:
            # Try to parse the date; handle common formats
            raw = str(last_traffic_at_raw).strip()
            # pandas NaT check
            if raw in ("NaT", "nat"):
                return "stale"
            last_dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(days=90)
            if last_dt < cutoff:
                return "stale"
        except Exception:
            return "stale"

    return "active"


def _compute_risk_score(row: dict, lazarus_status: str) -> int:
    """
    Compute risk_score (0–100) for an API.
    +30 if auth_type in ("none", "basic")
    +20 if tls_version in ("TLS1.0", "TLS1.1", "none")
    +20 if pii_exposure == true
    +15 if has_rate_limit == false
    +15 if lazarus_status in ("zombie", "shadow")
    """
    score = 0

    auth_type = str(row.get("auth_type", "")).strip().lower()
    if auth_type in ("none", "basic"):
        score += 30

    tls = str(row.get("tls_version", "")).strip().lower()
    if tls in ("tls1.0", "tls1.1", "tls 1.0", "tls 1.1", "none"):
        score += 20

    if _to_bool(row.get("pii_exposure", False)):
        score += 20

    if not _to_bool(row.get("has_rate_limit", True)):
        score += 15

    if lazarus_status in ("zombie", "shadow"):
        score += 15

    return min(score, 100)


def _row_to_doc(row: dict) -> dict:
    """Convert a CSV row dict to a MongoDB document with classification."""
    lazarus_status = _classify(row)
    risk_score = _compute_risk_score(row, lazarus_status)

    # Normalise last_traffic_at
    lta = str(row.get("last_traffic_at", "")).strip()
    if lta.lower() in ("", "none", "null", "nat"):
        lta = None

    return {
        "api_id": str(row["api_id"]).strip(),
        "name": str(row.get("name", "")).strip(),
        "path": str(row.get("path", "")).strip(),
        "method": str(row.get("method", "GET")).strip().upper(),
        "status": str(row.get("status", "active")).strip().lower(),
        "is_documented": _to_bool(row.get("is_documented", True)),
        "traffic_30d": _to_int(row.get("traffic_30d", 0)),
        "last_traffic_at": lta,
        "auth_type": str(row.get("auth_type", "")).strip(),
        "tls_version": str(row.get("tls_version", "")).strip(),
        "pii_exposure": _to_bool(row.get("pii_exposure", False)),
        "has_rate_limit": _to_bool(row.get("has_rate_limit", True)),
        "owner": str(row.get("owner", "")).strip(),
        "department": str(row.get("department", "")).strip(),
        "version": str(row.get("version", "")).strip(),
        "description": str(row.get("description", "")).strip(),
        "lazarus_status": lazarus_status,
        "risk_score": risk_score,
        "ingested_at": datetime.utcnow().isoformat() + "Z",
    }


# ── POST /catalog/upload ──

@router.post("/upload")
async def upload_catalog(
    file: UploadFile = File(...),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Upload a CSV containing the API inventory and live-probe every entry.

    Required columns:  api_id, url, method
    Optional column:   last_traffic_at  (ISO-8601 timestamp)

    Lazarus probes each URL live and classifies it as:
        ZOMBIE  — unreachable / timed out
        STALE   — no recent traffic signal
        ACTIVE  — reachable and recently active

    Results are upserted into MongoDB api_catalog and a summary is returned.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=422,
            detail={"detail": "Only .csv files are accepted.", "code": "INVALID_FILE_TYPE"},
        )

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents), dtype=str, keep_default_na=False)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={"detail": f"Failed to parse CSV: {e}", "code": "CSV_PARSE_ERROR"},
        )

    # Normalise column names
    df.columns = df.columns.str.strip().str.lower()
    cols = set(df.columns)

    # Validate minimum required columns
    missing = PROBE_REQUIRED_COLUMNS - cols
    if missing:
        raise HTTPException(
            status_code=422,
            detail={
                "detail": f"CSV is missing required columns: {sorted(missing)}",
                "code": "MISSING_COLUMNS",
            },
        )

    # ── Parse rows ────────────────────────────────────────────────────────────
    apis_to_probe = []
    errors = []

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        api_id = str(row_dict.get("api_id", "")).strip()
        url    = str(row_dict.get("url", "")).strip()
        method = str(row_dict.get("method", "GET")).strip().upper() or "GET"

        if not api_id:
            errors.append({"row": int(idx) + 2, "error": "Missing api_id"})
            continue
        if not url:
            errors.append({"row": int(idx) + 2, "api_id": api_id, "error": "Missing url"})
            continue

        entry = {k: str(v).strip() for k, v in row_dict.items() if str(v).strip() not in ("", "none", "null", "nan", "nat")}
        entry.update({"api_id": api_id, "url": url, "method": method})

        # last_traffic_at is optional (ensure we nullify if it's essentially empty)
        lta = entry.get("last_traffic_at", "")
        if isinstance(lta, str) and lta.lower() in ("", "none", "null", "nan", "nat"):
            entry["last_traffic_at"] = None
        elif lta:
            try:
                dt = pd.to_datetime(lta, format='mixed', dayfirst=True)
                entry["last_traffic_at"] = dt.isoformat()
            except Exception:
                pass

        try:
            validated = APIRow(**entry)
            entry["url"] = str(validated.url)
            entry["method"] = validated.method
        except ValidationError as e:
            error_msg = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
            errors.append({"row": int(idx) + 2, "api_id": api_id, "error": f"Validation failed: {error_msg}"})
            continue

        apis_to_probe.append(entry)

    if not apis_to_probe:
        raise HTTPException(
            status_code=422,
            detail={
                "detail": "No valid API rows found in CSV.",
                "code": "EMPTY_CSV",
                "parse_errors": errors,
            },
        )

    # ── Live probe (concurrent, capped at 10) ─────────────────────────────────
    probe_results = await probe_and_classify(apis_to_probe)

    # ── Upsert + count ────────────────────────────────────────────────────────
    # Frontend reads lowercase keys: zombie / shadow / stale / active
    status_counts = {"zombie": 0, "shadow": 0, "stale": 0, "active": 0}
    uploaded = 0
    updated  = 0

    for result in probe_results:
        try:
            doc = {
                **result,
                "ingested_at": datetime.utcnow().isoformat() + "Z",
            }
            existing = await db.get_api_catalog_by_id(result["api_id"])
            await db.upsert_api_catalog(doc)
            if existing:
                updated += 1
            else:
                uploaded += 1

            ls = result.get("lazarus_status", "ACTIVE").lower()
            if ls in status_counts:
                status_counts[ls] += 1
        except Exception as e:
            errors.append({"api_id": result.get("api_id"), "error": str(e)})

    await db.log_activity(
        "catalog_upload",
        file.filename,
        (
            f"Probe upload: {uploaded} new, {updated} updated — "
            f"zombie={status_counts['zombie']}, stale={status_counts['stale']}, "
            f"active={status_counts['active']}, errors={len(errors)}"
        ),
    )

    return {
        "uploaded": uploaded,
        "updated": updated,
        "total": uploaded + updated,
        "classification_summary": status_counts,
        "errors": errors,
        "filename": file.filename,
    }


# ── POST /catalog/probe-upload ────────────────────────────────────────────────

@router.post("/probe-upload")
async def probe_upload(
    file: UploadFile = File(...),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Upload a 4-column CSV (api_id, url, method are required; last_traffic_at
    is optional) and live-probe every API.

    Expected CSV columns:
        api_id          — unique identifier
        url             — full URL to probe  (e.g. https://api.example.com/payments)
        method          — HTTP method        (GET, POST, PUT, …)
        last_traffic_at — ISO-8601 timestamp (optional)

    Lazarus classifies each API as ZOMBIE | STALE | ACTIVE (SHADOW detection
    is reserved for a future phase — all CSV-sourced entries are in_catalog=True).

    Results are upserted into the MongoDB api_catalog collection and a JSON
    summary is returned.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=422,
            detail={"detail": "Only .csv files are accepted.", "code": "INVALID_FILE_TYPE"},
        )

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents), dtype=str, keep_default_na=False)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={"detail": f"Failed to parse CSV: {e}", "code": "CSV_PARSE_ERROR"},
        )

    # Normalise column names
    df.columns = df.columns.str.strip().str.lower()
    cols = set(df.columns)

    # Validate minimum required columns
    missing = PROBE_REQUIRED_COLUMNS - cols
    if missing:
        raise HTTPException(
            status_code=422,
            detail={
                "detail": f"CSV is missing required columns: {sorted(missing)}",
                "code": "MISSING_COLUMNS",
            },
        )

    # Build the list of API dicts to probe
    apis_to_probe = []
    parse_errors = []
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        api_id = str(row_dict.get("api_id", "")).strip()
        url = str(row_dict.get("url", "")).strip()
        method = str(row_dict.get("method", "GET")).strip().upper() or "GET"

        if not api_id:
            parse_errors.append({"row": int(idx) + 2, "error": "Missing api_id"})
            continue
        if not url:
            parse_errors.append({"row": int(idx) + 2, "api_id": api_id, "error": "Missing url"})
            continue

        entry = {"api_id": api_id, "url": url, "method": method}

        # last_traffic_at is optional — include only when the column exists and has a value
        if "last_traffic_at" in row_dict:
            lta = str(row_dict["last_traffic_at"]).strip()
            if lta.lower() in ("", "none", "null", "nat"):
                entry["last_traffic_at"] = None
            else:
                try:
                    dt = pd.to_datetime(lta, format='mixed', dayfirst=True)
                    entry["last_traffic_at"] = dt.isoformat()
                except Exception:
                    entry["last_traffic_at"] = lta

        try:
            validated = APIRow(**entry)
            entry["url"] = str(validated.url)
            entry["method"] = validated.method
        except ValidationError as e:
            error_msg = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
            parse_errors.append({"row": int(idx) + 2, "api_id": api_id, "error": f"Validation failed: {error_msg}"})
            continue

        apis_to_probe.append(entry)

    if not apis_to_probe:
        raise HTTPException(
            status_code=422,
            detail={
                "detail": "No valid API rows found in CSV.",
                "code": "EMPTY_CSV",
                "parse_errors": parse_errors,
            },
        )

    # ── Live probe (concurrent, capped at 10) ─────────────────────────────────
    probe_results = await probe_and_classify(apis_to_probe)

    # ── Upsert results into MongoDB ───────────────────────────────────────────
    status_counts = {"ZOMBIE": 0, "SHADOW": 0, "STALE": 0, "ACTIVE": 0}
    upsert_errors = []

    for result in probe_results:
        try:
            # Merge probe result into a catalog document
            doc = {
                **result,
                "ingested_at": datetime.utcnow().isoformat() + "Z",
            }
            await db.upsert_api_catalog(doc)

            ls = result.get("lazarus_status", "ACTIVE")
            if ls in status_counts:
                status_counts[ls] += 1
        except Exception as e:
            upsert_errors.append({"api_id": result.get("api_id"), "error": str(e)})

    await db.log_activity(
        "probe_upload",
        file.filename,
        (
            f"Probe upload: {len(probe_results)} probed — "
            f"ZOMBIE={status_counts['ZOMBIE']}, STALE={status_counts['STALE']}, "
            f"ACTIVE={status_counts['ACTIVE']}, parse_errors={len(parse_errors)}"
        ),
    )

    return {
        "total": len(probe_results),
        "classification_summary": status_counts,
        "parse_errors": parse_errors,
        "upsert_errors": upsert_errors,
        "filename": file.filename,
        "results": probe_results,
    }


# ── GET /catalog ──

@router.get("")
async def get_catalog():
    """Return all APIs from the MongoDB api_catalog collection."""
    docs = await db.get_all_api_catalog()
    return docs


# ── GET /catalog/export ──

@router.get("/export")
async def export_catalog():
    """Download the current api_catalog as a CSV file."""
    docs = await db.get_all_api_catalog()
    if not docs:
        raise HTTPException(
            status_code=404,
            detail={"detail": "No APIs in catalog. Upload a CSV first.", "code": "EMPTY_CATALOG"},
        )

    output = io.StringIO()
    writer = csv_module.DictWriter(output, fieldnames=SAMPLE_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for doc in docs:
        writer.writerow(doc)

    output.seek(0)
    filename = f"api_catalog_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── GET /catalog/sample ──

@router.get("/sample")
def get_sample_csv():
    """Download a sample CSV template showing the 4-column probe format."""
    sample_rows = [
        {
            "api_id": "API-001",
            "url": "https://api.yourbank.com/v2/payments",
            "method": "POST",
            "last_traffic_at": "2026-04-01T10:00:00Z",
        },
        {
            "api_id": "API-002",
            "url": "https://api.yourbank.com/v1/legacy/auth",
            "method": "GET",
            "last_traffic_at": "2025-10-15T09:22:00Z",
        },
        {
            "api_id": "API-003",
            "url": "https://api.yourbank.com/internal/admin",
            "method": "POST",
            "last_traffic_at": "",
        },
        {
            "api_id": "API-004",
            "url": "https://api.yourbank.com/v3/experimental/crypto-swap",
            "method": "PUT",
            "last_traffic_at": "2025-06-01T00:00:00Z",
        },
    ]

    output = io.StringIO()
    writer = csv_module.DictWriter(output, fieldnames=SAMPLE_COLUMNS)
    writer.writeheader()
    writer.writerows(sample_rows)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="api_probe_template.csv"'},
    )


# ── GET /catalog/{api_id} ──

@router.get("/{api_id}")
async def get_catalog_api(api_id: str):
    """Return a single API record from the catalog by api_id."""
    doc = await db.get_api_catalog_by_id(api_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail={"detail": f"API '{api_id}' not found in catalog.", "code": "NOT_FOUND"},
        )
    return doc
