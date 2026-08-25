from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext
import logging

from sentinelayer.backend.internal.auth.jwt_handler import create_access_token

router = APIRouter()
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    tenant_id: str

users_db = {
    "test@example.com": {
        "user_id": "user-123",
        "tenant_id": "tenant-acme",
        "password_hash": "$2b$12$KxG5YqKxG5YqKxG5YqKxG5YqKxG5YqKxG5YqKxG5YqKxG5YqKxG5YqKxG5",
        "roles": ["user"]
    }
}

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    user = users_db.get(request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    try:
        if not pwd_context.verify(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
    except Exception:
        raise HTTPException(status_code=500, detail="Authentication error")

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
