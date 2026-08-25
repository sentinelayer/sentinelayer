from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from datetime import timedelta
import uuid
import logging
import jwt
import time

from sentinelayer.backend.internal.auth.jwt_handler import create_access_token

router = APIRouter()
logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    tenant_id: str

# Simple user DB (tanpa bcrypt dulu)
users_db = {
    "test@example.com": {
        "user_id": "user-123",
        "tenant_id": "tenant-acme",
        "password": "password123",  # Plaintext sementara
        "roles": ["user"]
    }
}

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    user = users_db.get(request.email)
    if not user or user["password"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token_data = {
        "sub": user["user_id"],
        "tenant_id": user["tenant_id"],
        "email": request.email,
        "roles": user.get("roles", []),
    }
    
    access_token = create_access_token(token_data)
    
    return LoginResponse(
        access_token=access_token,
        expires_in=15 * 60,
        user_id=user["user_id"],
        tenant_id=user["tenant_id"]
    )
