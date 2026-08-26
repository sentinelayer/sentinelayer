import os
import jwt
import bcrypt
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from control_plane.app.infrastructure.db.session import get_db
from control_plane.app.infrastructure.db.models import User, Tenant

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


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


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
    expiry = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRY_MINUTES)
    token = jwt.encode(
        {
            "sub": user.id,
            "email": user.email,
            "tenant_id": user.tenant_id,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
            "exp": expiry,
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return TokenResponse(access_token=token, token_type="bearer", expires_in=JWT_EXPIRY_MINUTES * 60)
