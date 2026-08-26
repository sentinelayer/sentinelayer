import json
import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
import pyotp
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from control_plane.app.infrastructure.db.models import Tenant, User
from control_plane.app.infrastructure.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required")

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 15


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    tenant_id: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    mfa_required: bool = False


class MFASetupResponse(BaseModel):
    secret: str
    otpauth_url: str
    backup_codes: list[str]


class MFAVerifyRequest(BaseModel):
    code: str


def _make_token(user: User) -> TokenResponse:
    expiry = datetime.now(UTC) + timedelta(minutes=JWT_EXPIRY_MINUTES)
    token = jwt.encode(
        {
            "sub": user.id,
            "email": user.email,
            "tenant_id": user.tenant_id,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
            "mfa_enabled": bool(user.mfa_enabled),
            "exp": expiry,
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=JWT_EXPIRY_MINUTES * 60,
        mfa_required=False,
    )


def _user_from_bearer(authorization: str | None, db: Session) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if len(req.password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters")
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    tenant = db.query(Tenant).filter(Tenant.id == req.tenant_id).first()
    if not tenant:
        tenant = Tenant(id=req.tenant_id, name=f"tenant-{req.tenant_id[:8]}")
        db.add(tenant)
        db.flush()
    hashed = bcrypt.hashpw(req.password.encode("utf-8"), bcrypt.gensalt())
    user = User(
        id=str(uuid.uuid4()),
        email=req.email,
        hashed_password=hashed.decode("utf-8"),
        full_name=req.full_name,
        tenant_id=req.tenant_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "tenant_id": user.tenant_id}


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not bcrypt.checkpw(req.password.encode("utf-8"), user.hashed_password.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.mfa_enabled:
        if not req.mfa_code:
            return TokenResponse(
                access_token="",
                token_type="bearer",
                expires_in=0,
                mfa_required=True,
            )
        totp = pyotp.TOTP(user.mfa_secret or "")
        ok = totp.verify(req.mfa_code, valid_window=1)
        if not ok and user.mfa_backup_codes:
            codes = json.loads(user.mfa_backup_codes)
            if req.mfa_code in codes:
                codes.remove(req.mfa_code)
                user.mfa_backup_codes = json.dumps(codes)
                db.commit()
                ok = True
        if not ok:
            raise HTTPException(status_code=401, detail="Invalid MFA code")

    return _make_token(user)


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def mfa_setup(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_bearer(authorization, db)
    secret = pyotp.random_base32()
    backup = [secrets.token_hex(4) for _ in range(8)]
    user.mfa_secret = secret
    user.mfa_backup_codes = json.dumps(backup)
    user.mfa_enabled = False  # enable after verify
    db.commit()
    totp = pyotp.TOTP(secret)
    url = totp.provisioning_uri(name=user.email, issuer_name="SentinelLayer")
    return MFASetupResponse(secret=secret, otpauth_url=url, backup_codes=backup)


@router.post("/mfa/verify")
async def mfa_verify(
    req: MFAVerifyRequest,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_bearer(authorization, db)
    if not user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA not set up")
    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(req.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid code")
    user.mfa_enabled = True
    db.commit()
    return {"mfa_enabled": True}


@router.post("/mfa/disable")
async def mfa_disable(
    req: MFAVerifyRequest,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_bearer(authorization, db)
    if not user.mfa_enabled:
        return {"mfa_enabled": False}
    totp = pyotp.TOTP(user.mfa_secret or "")
    if not totp.verify(req.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid code")
    user.mfa_enabled = False
    user.mfa_secret = None
    user.mfa_backup_codes = None
    db.commit()
    return {"mfa_enabled": False}


@router.get("/me")
async def me(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    user = _user_from_bearer(authorization, db)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "tenant_id": user.tenant_id,
        "is_admin": user.is_admin,
        "mfa_enabled": bool(user.mfa_enabled),
    }
