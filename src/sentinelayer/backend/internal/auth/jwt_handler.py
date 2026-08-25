from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from pydantic import BaseModel

class TokenPayload(BaseModel):
    sub: str  # user_id
    tenant_id: str
    exp: datetime

    # Application Context dari blueprint Section 11.22
    application_id: str | None = None
    session_id: str | None = None

class JWTConfig:
    SECRET_KEY = "CHANGE_ME_IN_KMS"  # Nanti di-replace pake KMS (Section 8.12)
    ALGORITHM = "RS256"  # Blueprint minta RS256
    ACCESS_TOKEN_EXPIRE_MINUTES = 15

def create_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    # TODO: Sign pake private key dari KMS (Section 8.12)
    return jwt.encode(to_encode, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM)

def verify_token(token: str) -> TokenPayload | None:
    try:
        payload = jwt.decode(token, JWTConfig.SECRET_KEY, algorithms=[JWTConfig.ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None
