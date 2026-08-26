from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    tenant_id: str

class LoginRequest(BaseModel):
    email: str
    password: str

users_db = {}

@router.post("/register")
async def register(req: RegisterRequest):
    if req.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    users_db[req.email] = {
        "password": req.password,
        "full_name": req.full_name,
        "tenant_id": req.tenant_id
    }
    return {
        "id": str(uuid.uuid4()),
        "email": req.email,
        "full_name": req.full_name,
        "tenant_id": req.tenant_id,
        "message": "User registered successfully"
    }

@router.post("/login")
async def login(req: LoginRequest):
    user = users_db.get(req.email)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "access_token": "fake-jwt-token",
        "token_type": "bearer",
        "expires_in": 900
    }
