from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, EmailStr
from datetime import timedelta
import uuid
import logging

from sentinelayer.backend.internal.auth.jwt_handler import create_access_token, verify_token

router = APIRouter()
logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    tenant_id: str

class RefreshRequest(BaseModel):
    refresh_token: str

class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# Mock user database (sementara)
users_db = {
    "test@example.com": {
        "user_id": "user-123",
        "tenant_id": "tenant-acme",
        "password": "password123",  # Di real, pake hashed
        "roles": ["user"]
    }
}

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login endpoint - returns JWT token"""
    
    # Validate user (mock)
    user = users_db.get(request.email)
    if not user or user["password"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create token payload
    token_data = {
        "sub": user["user_id"],
        "tenant_id": user["tenant_id"],
        "email": request.email,
        "roles": user.get("roles", []),
        "application_id": "sentinel-layer",
        "session_id": str(uuid.uuid4())
    }
    
    access_token = create_access_token(token_data)
    
    return LoginResponse(
        access_token=access_token,
        expires_in=15 * 60,  # 15 minutes in seconds
        user_id=user["user_id"],
        tenant_id=user["tenant_id"]
    )

@router.post("/validate")
async def validate_token(request: Request):
    """Validate JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scheme"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid header format"
        )
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return {
        "valid": True,
        "user_id": payload.sub,
        "tenant_id": payload.tenant_id,
        "email": payload.email,
        "roles": payload.roles,
        "expires_at": payload.exp.isoformat()
    }

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: RefreshRequest):
    """Refresh access token"""
    # For now, just create new token
    # In real implementation, validate refresh token
    token_data = {
        "sub": "user-123",
        "tenant_id": "tenant-acme",
        "email": "test@example.com",
        "roles": ["user"]
    }
    
    access_token = create_access_token(token_data)
    
    return RefreshResponse(
        access_token=access_token,
        expires_in=15 * 60
    )
