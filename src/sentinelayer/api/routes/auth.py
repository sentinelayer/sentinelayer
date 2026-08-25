from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import timedelta
import jwt
import time

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    # Buat token sederhana (ga pake JWT library dulu)
    payload = {
        "sub": "user-123",
        "tenant_id": "tenant-acme",
        "exp": int(time.time()) + 900
    }
    
    # Pake HS256 (sederhana)
    secret = "CHANGE_ME_IN_PRODUCTION"
    token = jwt.encode(payload, secret, algorithm="HS256")
    
    return LoginResponse(
        access_token=token,
        expires_in=900
    )
