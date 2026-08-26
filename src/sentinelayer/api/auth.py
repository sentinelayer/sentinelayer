import jwt
import os
import bcrypt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from src.sentinelayer.database import get_db
from src.sentinelayer.database.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-key-change-in-production")
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
    
    hashed = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt())
    
    user = User(
        email=req.email,
        hashed_password=hashed.decode('utf-8'),
        full_name=req.full_name,
        tenant_id=req.tenant_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "full_name": user.full_name}

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not bcrypt.checkpw(req.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    expiry = datetime.utcnow() + timedelta(minutes=JWT_EXPIRY_MINUTES)
    token = jwt.encode(
        {
            "sub": user.id,
            "email": user.email,
            "tenant_id": user.tenant_id,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
            "exp": expiry
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    return TokenResponse(access_token=token, token_type="bearer", expires_in=JWT_EXPIRY_MINUTES * 60)
