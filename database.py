"""
database.py — Async MongoDB persistence for Lazarus (motor).
Connection: mongodb://127.0.0.1:27017/lazarus
"""

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGO_URI = "mongodb://127.0.0.1:27017/lazarus"

client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = client["lazarus"]

# Collections
decommissions = db["decommissions"]
honeypots = db["honeypots"]
activity_log = db["activity_log"]
redirect_rules = db["redirect_rules"]
api_catalog = db["api_catalog"]
users = db["users"]
status_change_log = db["status_change_log"]
audit_log = db["audit_log"]
security_events = db["security_events"]
scan_metadata = db["scan_metadata"]
invite_codes = db["invite_codes"]

# ── Invite Code Operations ──

async def create_invite_code(doc: dict):
    """Insert a new invite code."""
    try:
        await invite_codes.insert_one(doc)
    except Exception as e:
        print(f"[DB] Failed to create invite code: {e}")


async def get_invite_code(code: str) -> dict | None:
    """Return an invite code document by its code string."""
    try:
        return await invite_codes.find_one({"code": code}, {"_id": 0})
    except Exception:
        return None


async def mark_invite_code_used(code: str):
    """Mark an invite code as used."""
    try:
        await invite_codes.update_one(
            {"code": code},
            {"$set": {
                "is_used": True,
                "used_at": datetime.utcnow().isoformat() + "Z"
            }}
        )
    except Exception as e:
        print(f"[DB] Failed to mark invite code as used: {e}")


async def revoke_invite_code(code: str):
    """Mark an invite code as inactive (revoked)."""
    try:
        await invite_codes.update_one(
            {"code": code},
            {"$set": {"is_active": False}}
        )
    except Exception as e:
        print(f"[DB] Failed to revoke invite code: {e}")


# ── Decommission Operations ──

async def save_decommission(entry: dict):
    """Save a decommission record. Uses path as unique key."""
    entry["_id"] = entry["path"]  # prevent duplicates
    try:
        await decommissions.replace_one({"_id": entry["path"]}, entry, upsert=True)
    except Exception as e:
        print(f"[DB] Failed to save decommission: {e}")
    await log_activity("decommission", entry.get("path"), f"Decommissioned {entry.get('path')}")


async def get_all_decommissions() -> list:
    """Return all decommission records."""
    try:
        return await decommissions.find({}, {"_id": 0}).to_list(length=None)
    except Exception as e:
        print(f"[DB] Failed to read decommissions: {e}")
        return []


async def is_decommissioned(path: str) -> bool:
    """Check if an API path has already been decommissioned."""
    try:
        return await decommissions.find_one({"path": path}) is not None
    except Exception:
        return False


async def get_decommission_by_path(path: str) -> dict | None:
    """Get a single decommission record by path."""
    try:
        doc = await decommissions.find_one({"path": path}, {"_id": 0})
        return doc
    except Exception:
        return None


# ── Honeypot Operations ──

async def save_honeypot(path: str):
    """Record a honeypot deployment."""
    try:
        await honeypots.replace_one(
            {"_id": path},
            {"_id": path, "path": path, "deployed_at": datetime.utcnow().isoformat() + "Z"},
            upsert=True,
        )
    except Exception as e:
        print(f"[DB] Failed to save honeypot: {e}")
    await log_activity("honeypot", path, f"Honeypot deployed on {path}")


async def get_all_honeypots() -> list:
    """Return all deployed honeypot paths."""
    try:
        docs = await honeypots.find({}, {"_id": 0, "path": 1}).to_list(length=None)
        return [doc["path"] for doc in docs]
    except Exception:
        return []


# ── Activity Log ──

async def log_activity(action: str, target: str, detail: str):
    """Append an entry to the activity log."""
    try:
        await activity_log.insert_one({
            "action": action,
            "target": target,
            "detail": detail,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
    except Exception as e:
        print(f"[DB] Failed to log activity: {e}")


# ── Audit Log ──

async def save_audit_entry(entry: dict):
    """Save an audit log entry."""
    try:
        await audit_log.insert_one(entry)
    except Exception as e:
        print(f"[DB] Failed to save audit log: {e}")

async def get_audit_log(limit: int = 50) -> list:
    """Return recent audit log entries."""
    try:
        return await (
            audit_log.find({}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
            .to_list(length=None)
        )
    except Exception:
        return []


async def get_activity_log(limit: int = 50) -> list:
    """Return recent activity log entries."""
    try:
        return await (
            activity_log.find({}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
            .to_list(length=None)
        )
    except Exception:
        return []


async def get_honeypot_activity(limit: int = 100) -> list:
    """Return all activity_log documents where action is honeypot_hit, sorted descending."""
    try:
        return await (
            activity_log.find({"action": "honeypot_hit"}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
            .to_list(length=None)
        )
    except Exception:
        return []


# ── Redirect Rules ──

async def save_redirect_rule(old_path: str, new_path: str):
    """Save a redirect rule mapping old_path → new_path."""
    try:
        await redirect_rules.replace_one(
            {"_id": old_path},
            {
                "_id": old_path,
                "old_path": old_path,
                "new_path": new_path,
                "created_at": datetime.utcnow().isoformat() + "Z",
            },
            upsert=True,
        )
    except Exception as e:
        print(f"[DB] Failed to save redirect rule: {e}")


async def get_redirect_rule(old_path: str) -> str | None:
    """Return new_path for old_path if a redirect rule exists, else None."""
    try:
        doc = await redirect_rules.find_one({"_id": old_path}, {"new_path": 1})
        return doc["new_path"] if doc else None
    except Exception:
        return None


async def get_all_redirect_rules() -> list:
    """Return all saved redirect rules."""
    try:
        return await redirect_rules.find({}, {"_id": 0}).to_list(length=None)
    except Exception:
        return []


# ── API Catalog Operations ──

async def upsert_api_catalog(doc: dict):
    """Upsert an API record into the api_catalog collection keyed on api_id."""
    try:
        await api_catalog.replace_one(
            {"api_id": doc["api_id"]},
            doc,
            upsert=True,
        )
    except Exception as e:
        print(f"[DB] Failed to upsert api_catalog: {e}")


async def get_all_api_catalog() -> list:
    """Return all APIs from the api_catalog collection (excluding MongoDB _id)."""
    try:
        return await api_catalog.find({}, {"_id": 0}).to_list(length=None)
    except Exception:
        return []


async def get_api_catalog_by_id(api_id: str) -> dict | None:
    """Return a single API record by api_id."""
    try:
        return await api_catalog.find_one({"api_id": api_id}, {"_id": 0})
    except Exception:
        return None


async def get_api_catalog_count() -> int:
    """Return the number of documents in api_catalog."""
    try:
        return await api_catalog.count_documents({})
    except Exception:
        return 0


# ── User Operations ──

async def create_user(user_doc: dict):
    """Insert a new user document."""
    try:
        await users.insert_one(user_doc)
    except Exception as e:
        raise Exception(f"Failed to create user: {e}")


async def get_user_by_email(email: str) -> dict | None:
    """Return a user document by email."""
    try:
        return await users.find_one({"email": email}, {"_id": 0})
    except Exception:
        return None


async def update_user_last_login(email: str):
    """Update last_login timestamp for a user."""
    try:
        await users.update_one(
            {"email": email},
            {"$set": {"last_login": datetime.utcnow().isoformat() + "Z"}},
        )
    except Exception as e:
        print(f"[DB] Failed to update last_login: {e}")


# ── Status Change Log ──

async def log_status_change(api_id: str, old_status: str, new_status: str):
    """Log a status change to the status_change_log collection."""
    try:
        await status_change_log.insert_one({
            "api_id": api_id,
            "old_status": old_status,
            "new_status": new_status,
            "message": f"{api_id} changed from {old_status} to {new_status} at {datetime.utcnow().isoformat()}Z",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
    except Exception as e:
        print(f"[DB] Failed to log status change: {e}")


async def get_status_changes(limit: int = 200) -> list:
    """Return recent status change log entries."""
    try:
        return await (
            status_change_log.find({}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
            .to_list(length=None)
        )
    except Exception:
        return []


# ── Health Check ──

async def is_connected() -> bool:
    """Check if MongoDB is reachable."""
    try:
        await client.admin.command("ping")
        return True
    except Exception:
        return False


# ── Security Events ──

async def save_security_event(event: dict):
    """Insert a security anomaly event."""
    try:
        await security_events.insert_one(event)
    except Exception as e:
        print(f"[DB] Failed to save security event: {e}")


async def get_security_events(limit: int = 200) -> list:
    """Return recent security events, newest first."""
    try:
        return await (
            security_events.find({}, {"_id": 0})
            .sort("detected_at", -1)
            .limit(limit)
            .to_list(length=None)
        )
    except Exception:
        return []


# ── Scan Metadata ──

async def upsert_scan_metadata(doc: dict):
    """Upsert the latest scan run metadata (keyed on 'latest')."""
    try:
        await scan_metadata.replace_one(
            {"_id": "latest"},
            {**doc, "_id": "latest"},
            upsert=True,
        )
    except Exception as e:
        print(f"[DB] Failed to upsert scan_metadata: {e}")


async def get_scan_metadata() -> dict | None:
    """Return the latest scan metadata document."""
    try:
        return await scan_metadata.find_one({"_id": "latest"}, {"_id": 0})
    except Exception:
        return None

