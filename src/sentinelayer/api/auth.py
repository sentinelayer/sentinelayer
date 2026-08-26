import os
import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from src.sentinelayer.database import get_db
from src.sentinelayer.database.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.environ["JWT_SECRET"]
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

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=req.email,
        hashed_password=pwd_context.hash(req.password),
        full_name=req.full_name,
        tenant_id=req.tenant_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "email": user.email}

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not pwd_context.verify(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    expiry = datetime.utcnow() + timedelta(minutes=JWT_EXPIRY_MINUTES)
    token = jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
            "is_admin": user.is_admin,
            "exp": expiry
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=JWT_EXPIRY_MINUTES * 60
    )
