"""
admin.py — Admin routes for Lazarus platform.
"""

import os
import secrets
import uuid
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Header, HTTPException

import database as db

router = APIRouter(prefix="/admin", tags=["Admin"])

# The ADMIN_KEY should be passed in headers, e.g., X-Admin-Key

async def verify_admin_key(x_admin_key: str = Header(None)):
    """Dependency to check the admin key."""
    # Note: ADMIN_KEY from .env is manually inserted by the user as per instructions.
    expected_key = os.getenv("ADMIN_KEY")
    if not expected_key or x_admin_key != expected_key:
        raise HTTPException(status_code=403, detail="Forbidden. Invalid or missing Admin Key.")


class InviteRequest(BaseModel):
    created_for: str


@router.post("/invite", dependencies=[__import__("fastapi").Depends(verify_admin_key)])
async def generate_invite(req: InviteRequest):
    """Generate a unique invite code for a user."""
    code = secrets.token_urlsafe(16)
    
    doc = {
        "id": str(uuid.uuid4()),
        "code": code,
        "created_for": req.created_for,
        "is_used": False,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "used_at": None,
    }
    
    await db.create_invite_code(doc)
    
    return {
        "message": "Invite code generated successfully.",
        "invite_code": code,
        "created_for": req.created_for
    }


@router.post("/invite/{code}/revoke", dependencies=[__import__("fastapi").Depends(verify_admin_key)])
async def revoke_invite(code: str):
    """Revoke an invite code to prevent its usage."""
    invite = await db.get_invite_code(code)
    if not invite:
        raise HTTPException(status_code=404, detail="Invite code not found.")
    
    if invite.get("is_used"):
        raise HTTPException(status_code=400, detail="Cannot revoke an already used invite code.")
    
    if not invite.get("is_active"):
        return {"message": "Invite code is already revoked."}
        
    await db.revoke_invite_code(code)
    return {"message": "Invite code revoked successfully."}
