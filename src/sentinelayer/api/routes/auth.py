from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging

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

users_db = {
    "test@example.com": {
        "user_id": "user-123",
        "tenant_id": "tenant-acme",
        "password": "password123",
        "roles": ["user", "admin"]
    }
}

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    user = users_db.get(request.email)
    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return LoginResponse(
        access_token="valid-token-for-testing-12345",
        expires_in=900,
        user_id=user["user_id"],
        tenant_id=user["tenant_id"]
    )
