import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from control_plane.app.infrastructure.db.models import User
from control_plane.app.infrastructure.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])

class UserCreate(BaseModel):
    email: str
    full_name: str
    tenant_id: str

@router.post("/")
async def create_user(data: UserCreate, db: Session = Depends(get_db)):
    user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        full_name=data.full_name,
        tenant_id=data.tenant_id,
        hashed_password="placeholder"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "full_name": user.full_name}

@router.get("/")
async def list_users(tenant_id: str = None, db: Session = Depends(get_db)):
    query = db.query(User)
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    users = query.all()
    return [{"id": u.id, "email": u.email, "full_name": u.full_name} for u in users]
