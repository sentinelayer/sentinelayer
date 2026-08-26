from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from control_plane.app.infrastructure.db.session import get_db
from control_plane.app.infrastructure.db.models import Policy
from pydantic import BaseModel
import uuid
import json

router = APIRouter(prefix="/policies", tags=["policies"])

class PolicyCreate(BaseModel):
    name: str
    rules: dict
    application_id: str

@router.post("/")
async def create_policy(data: PolicyCreate, db: Session = Depends(get_db)):
    policy = Policy(
        id=str(uuid.uuid4()),
        name=data.name,
        rules=json.dumps(data.rules),
        application_id=data.application_id
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return {"id": policy.id, "name": policy.name}

@router.get("/")
async def list_policies(application_id: str = None, db: Session = Depends(get_db)):
    query = db.query(Policy)
    if application_id:
        query = query.filter_by(application_id=application_id)
    policies = query.all()
    return [{"id": p.id, "name": p.name} for p in policies]
