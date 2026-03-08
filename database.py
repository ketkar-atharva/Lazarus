"""
Database module — MongoDB persistence for Lazarus.
Connection: mongodb://127.0.0.1:27017/lazarus
"""

from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "mongodb://127.0.0.1:27017/lazarus"

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = client["lazarus"]

# Collections
decommissions = db["decommissions"]
honeypots = db["honeypots"]
activity_log = db["activity_log"]


# ── Decommission Operations ──

def save_decommission(entry: dict):
    """Save a decommission record. Uses path as unique key."""
    entry["_id"] = entry["path"]  # prevent duplicates
    try:
        decommissions.replace_one({"_id": entry["path"]}, entry, upsert=True)
    except Exception as e:
        print(f"[DB] Failed to save decommission: {e}")
    log_activity("decommission", entry.get("path"), f"Decommissioned {entry.get('path')}")


def get_all_decommissions() -> list:
    """Return all decommission records."""
    try:
        return list(decommissions.find({}, {"_id": 0}))
    except Exception as e:
        print(f"[DB] Failed to read decommissions: {e}")
        return []


def is_decommissioned(path: str) -> bool:
    """Check if an API path has already been decommissioned."""
    try:
        return decommissions.find_one({"path": path}) is not None
    except Exception:
        return False


def get_decommission_by_path(path: str) -> dict | None:
    """Get a single decommission record by path."""
    try:
        doc = decommissions.find_one({"path": path}, {"_id": 0})
        return doc
    except Exception:
        return None


# ── Honeypot Operations ──

def save_honeypot(path: str):
    """Record a honeypot deployment."""
    try:
        honeypots.replace_one(
            {"_id": path},
            {"_id": path, "path": path, "deployed_at": datetime.utcnow().isoformat() + "Z"},
            upsert=True,
        )
    except Exception as e:
        print(f"[DB] Failed to save honeypot: {e}")
    log_activity("honeypot", path, f"Honeypot deployed on {path}")


def get_all_honeypots() -> list:
    """Return all deployed honeypot paths."""
    try:
        return [doc["path"] for doc in honeypots.find({}, {"_id": 0, "path": 1})]
    except Exception:
        return []


# ── Activity Log ──

def log_activity(action: str, target: str, detail: str):
    """Append an entry to the activity log."""
    try:
        activity_log.insert_one({
            "action": action,
            "target": target,
            "detail": detail,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
    except Exception as e:
        print(f"[DB] Failed to log activity: {e}")


def get_activity_log(limit: int = 50) -> list:
    """Return recent activity log entries."""
    try:
        return list(
            activity_log.find({}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )
    except Exception:
        return []


# ── Health Check ──

def is_connected() -> bool:
    """Check if MongoDB is reachable."""
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False
