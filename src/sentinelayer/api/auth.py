from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import os
from sqlalchemy.orm import Session
from src.sentinelayer.database import get_db
from src.sentinelayer.database.models import User
from passlib.context import CryptContext

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not pwd_context.verify(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = jwt.encode(
        {"sub": str(user.id), "email": user.email, "exp": datetime.utcnow() + timedelta(minutes=15)},
        os.getenv("JWT_SECRET", "secret"),
        algorithm="HS256"
    )
    return {"access_token": token, "token_type": "bearer"}
