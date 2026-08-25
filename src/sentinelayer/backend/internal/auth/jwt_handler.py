import os
import time
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel

class TokenPayload(BaseModel):
    sub: str
    tenant_id: str
    exp: datetime
    email: Optional[str] = None
    roles: Optional[list] = []

class JWTConfig:
    @staticmethod
    def get_secret_key() -> str:
        # Kalo testing, pake fake secret (ga divalidasi)
        if os.getenv("TESTING", "false").lower() == "true":
            return "fake-secret-for-testing-only"
        
        secret = os.getenv("JWT_SECRET_KEY", "")
        if not secret or secret == "CHANGE_ME_IN_PRODUCTION_USE_KMS":
            raise RuntimeError(
                "JWT_SECRET_KEY must be set to a secure value in production! "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return secret
    
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "15"))

def create_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWTConfig.get_secret_key(), algorithm=JWTConfig.ALGORITHM)

def verify_token(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, JWTConfig.get_secret_key(), algorithms=[JWTConfig.ALGORITHM])
        return TokenPayload(**payload)
    except jwt.PyJWTError:
        return None

def create_access_token(data: Dict[str, Any]) -> str:
    return create_token(data)
