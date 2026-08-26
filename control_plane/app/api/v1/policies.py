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
    return {"id": policy.id, "name": policy.name, "rules": policy.rules}

@router.get("/")
async def list_policies(db: Session = Depends(get_db)):
    policies = db.query(Policy).all()
    return [{"id": p.id, "name": p.name} for p in policies]

@router.get("/{id}")
async def get_policy(id: str, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter_by(id=id).first()
    if not policy:
        return {"error": "Policy not found"}
    return {"id": policy.id, "name": policy.name, "rules": json.loads(policy.rules)}
