from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel
from jose import jwt, JWTError
import os

class TokenPayload(BaseModel):
    sub: str  # user_id
    tenant_id: str
    exp: datetime
    application_id: Optional[str] = None
    session_id: Optional[str] = None
    email: Optional[str] = None
    roles: Optional[list] = []

class JWTConfig:
    # Di production, ambil dari environment variable
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION_USE_KMS")
    ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))

def create_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM)

def verify_token(token: str) -> Optional[TokenPayload]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWTConfig.SECRET_KEY, algorithms=[JWTConfig.ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None

def create_access_token(data: Dict[str, Any]) -> str:
    """Create access token with default expiration"""
    return create_token(data)

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create refresh token with longer expiration"""
    return create_token(data, timedelta(days=JWTConfig.REFRESH_TOKEN_EXPIRE_DAYS))

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode token without validation (for debugging)"""
    try:
        return jwt.decode(token, JWTConfig.SECRET_KEY, algorithms=[JWTConfig.ALGORITHM], options={"verify_signature": False})
    except:
        return None
