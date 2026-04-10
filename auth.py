"""
auth.py — JWT authentication for Lazarus.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel
from dotenv import load_dotenv

import database as db

load_dotenv()

# ── Config ──
JWT_SECRET = os.getenv("JWT_SECRET", "lazarus-super-secret-jwt-key-change-in-production")
BANK_EMAIL_DOMAIN = os.getenv("BANK_EMAIL_DOMAIN", "@lazarusbank.com")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

# ── Crypto ──
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Pydantic Models ──

class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str
    employee_id: str
    department: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


# ── Helpers ──

def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def _safe_user(user_doc: dict) -> dict:
    """Remove sensitive fields before returning user to client."""
    return {k: v for k, v in user_doc.items() if k not in ("hashed_password", "_id")}


# ── Dependency: get_current_user ──

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validate JWT token and return the current user.
    Raises 401 if token is missing or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"detail": "Not authenticated. Please log in.", "code": "UNAUTHORIZED"},
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get_user_by_email(email)
    if not user:
        raise credentials_exception
    return _safe_user(user)


# ── POST /auth/signup ──

@router.post("/signup", status_code=201)
async def signup(req: SignupRequest):
    """
    Register a new bank employee account.
    Email must end with the configured BANK_EMAIL_DOMAIN.
    """
    if not req.email.lower().endswith(BANK_EMAIL_DOMAIN.lower()):
        raise HTTPException(
            status_code=422,
            detail={
                "detail": f"Email must be a bank address ending in {BANK_EMAIL_DOMAIN}",
                "code": "INVALID_EMAIL_DOMAIN",
            },
        )

    if len(req.password) < 8:
        raise HTTPException(
            status_code=422,
            detail={"detail": "Password must be at least 8 characters.", "code": "WEAK_PASSWORD"},
        )

    existing = await db.get_user_by_email(req.email.lower())
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"detail": "An account with this email already exists.", "code": "EMAIL_CONFLICT"},
        )

    user_doc = {
        "email": req.email.lower(),
        "hashed_password": _hash_password(req.password),
        "full_name": req.full_name,
        "employee_id": req.employee_id,
        "department": req.department,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "last_login": None,
    }

    try:
        await db.create_user(user_doc)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"Failed to create account: {e}", "code": "DB_ERROR"},
        )

    return {"message": "Account created successfully."}


# ── POST /auth/login ──

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a bank user and return a JWT access token.
    Uses OAuth2PasswordRequestForm (username = email).
    """
    email = form_data.username.lower()
    user = await db.get_user_by_email(email)

    if not user or not _verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=401,
            detail={"detail": "Invalid credentials.", "code": "INVALID_CREDENTIALS"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    await db.update_user_last_login(email)

    token = _create_access_token({"sub": email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _safe_user(user),
    }


# ── GET /auth/me ──

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user
