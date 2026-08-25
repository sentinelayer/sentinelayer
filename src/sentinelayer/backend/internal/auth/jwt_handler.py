from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import Optional

class TokenPayload(BaseModel):
    sub: str  # user_id
    tenant_id: str
    exp: datetime
    application_id: Optional[str] = None
    session_id: Optional[str] = None

class JWTConfig:
    SECRET_KEY = "CHANGE_ME_IN_PRODUCTION_USE_KMS"
    ALGORITHM = "HS256"  # Simpler for testing
    ACCESS_TOKEN_EXPIRE_MINUTES = 15

def create_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM)

def verify_token(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, JWTConfig.SECRET_KEY, algorithms=[JWTConfig.ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None
