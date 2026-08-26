from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from control_plane.app.infrastructure.db.session import get_db
from control_plane.app.infrastructure.db.models import Policy, Application
from pydantic import BaseModel
import uuid
import json

router = APIRouter(prefix="/policies", tags=["policies"])


class PolicyCreate(BaseModel):
    name: str
    rules: dict | list = {}
    application_id: str | None = None


def _tenant(request: Request) -> str:
    tid = getattr(request.state, "tenant_id", None)
    if not tid:
        raise HTTPException(status_code=400, detail="Missing tenant ID")
    return tid


@router.post("/")
@router.post("")
async def create_policy(data: PolicyCreate, request: Request, db: Session = Depends(get_db)):
    tenant_id = _tenant(request)
    app_id = data.application_id
    if app_id:
        app = db.query(Application).filter(Application.id == app_id, Application.tenant_id == tenant_id).first()
        if not app:
            raise HTTPException(status_code=404, detail="Application not found for tenant")
    policy = Policy(
        id=str(uuid.uuid4()),
        name=data.name,
        rules=json.dumps(data.rules),
        application_id=app_id or "",
    )
    # store tenant on policy if model has column; else bind via application
    if hasattr(policy, "tenant_id"):
        policy.tenant_id = tenant_id
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return {"id": policy.id, "name": policy.name, "tenant_id": tenant_id, "rules": data.rules}


@router.get("/")
@router.get("")
async def list_policies(request: Request, db: Session = Depends(get_db)):
    tenant_id = _tenant(request)
    # join via applications owned by tenant
    app_ids = [a.id for a in db.query(Application).filter(Application.tenant_id == tenant_id).all()]
    q = db.query(Policy)
    if hasattr(Policy, "tenant_id"):
        policies = q.filter(Policy.tenant_id == tenant_id).all()
    elif app_ids:
        policies = q.filter(Policy.application_id.in_(app_ids)).all()
    else:
        policies = []
    return [{"id": p.id, "name": p.name, "tenant_id": tenant_id} for p in policies]


@router.get("/{policy_id}")
async def get_policy(policy_id: str, request: Request, db: Session = Depends(get_db)):
    tenant_id = _tenant(request)
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Not found")
    if hasattr(policy, "tenant_id") and getattr(policy, "tenant_id", None) not in (None, "", tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    if policy.application_id:
        app = db.query(Application).filter(Application.id == policy.application_id).first()
        if app and app.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    rules = policy.rules
    try:
        rules = json.loads(policy.rules) if isinstance(policy.rules, str) else policy.rules
    except Exception:
        pass
    return {"id": policy.id, "name": policy.name, "rules": rules, "tenant_id": tenant_id}
