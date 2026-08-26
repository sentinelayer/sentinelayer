from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import Policy, Application
from pydantic import BaseModel, Field
from typing import Any, Optional
import uuid
import json

router = APIRouter(prefix="/policies", tags=["policies"])


class PolicyCreate(BaseModel):
    name: str
    rules: dict[str, Any] = Field(default_factory=dict)
    application_id: Optional[str] = None


@router.post("/")
@router.post("")
async def create_policy(data: PolicyCreate, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    if data.application_id:
        app = (
            db.query(Application)
            .filter(Application.id == data.application_id, Application.tenant_id == tid)
            .first()
        )
        if not app:
            raise HTTPException(status_code=404, detail="Application not found for tenant")
    policy = Policy(
        id=str(uuid.uuid4()),
        name=data.name,
        rules=json.dumps(data.rules),
        application_id=data.application_id,
        tenant_id=tid,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return {"id": policy.id, "name": policy.name, "tenant_id": tid, "rules": data.rules}


@router.get("/")
@router.get("")
async def list_policies(request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    policies = db.query(Policy).filter(Policy.tenant_id == tid).all()
    return [{"id": p.id, "name": p.name, "tenant_id": p.tenant_id} for p in policies]


@router.get("/{policy_id}")
async def get_policy(policy_id: str, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.tenant_id == tid).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Not found")
    rules = policy.rules
    try:
        rules = json.loads(policy.rules) if isinstance(policy.rules, str) else policy.rules
    except Exception:
        pass
    return {"id": policy.id, "name": policy.name, "rules": rules, "tenant_id": policy.tenant_id}
