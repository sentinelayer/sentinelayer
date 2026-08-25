from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel

class TokenPayload(BaseModel):
    sub: str
    tenant_id: str
    exp: datetime
    application_id: Optional[str] = None
    session_id: Optional[str] = None

class JWTConfig:
    SECRET_KEY = "CHANGE_ME_IN_PRODUCTION_USE_KMS"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15

def create_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    # Untuk sementara pake fake token
    import uuid
    return f"fake-token-{uuid.uuid4()}-{int(expire.timestamp())}"

def verify_token(token: str) -> Optional[TokenPayload]:
    # Untuk sementara, validasi fake token
    if token and token.startswith("fake-token-"):
        parts = token.split("-")
        if len(parts) >= 4:
            return TokenPayload(
                sub="user-123",
                tenant_id="tenant-acme",
                exp=datetime.now(timezone.utc) + timedelta(minutes=15)
            )
    return None
