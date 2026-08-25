from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from sentinelayer.backend.internal.auth.jwt_handler import create_token, verify_token

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
    """Login endpoint - returns JWT token"""
    
    # TODO: Validate credentials from database
    # For now, accept any email/password for testing
    if not request.email or not request.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password required"
        )
    
    # Create token (in production, validate against DB)
    token_data = {
        "sub": "user-123",
        "tenant_id": "tenant-acme",
        "application_id": "payment-api",
        "session_id": "sess-xyz"
    }
    
    access_token = create_token(token_data, expires_delta=timedelta(minutes=15))
    
    return LoginResponse(
        access_token=access_token,
        expires_in=900  # 15 minutes
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
        "expires_at": payload.exp.isoformat()
    }
