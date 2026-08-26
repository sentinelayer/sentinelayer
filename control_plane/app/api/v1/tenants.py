
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from control_plane.app.infrastructure.db.models import Tenant
from control_plane.app.infrastructure.db.session import get_db

router = APIRouter(prefix="/tenants", tags=["tenants"])


class TenantCreate(BaseModel):
    name: str


def _tenant(request: Request) -> str:
    tid = getattr(request.state, "tenant_id", None)
    if not tid:
        raise HTTPException(status_code=400, detail="Missing tenant ID")
    return tid


@router.post("/")
@router.post("")
async def create_tenant(data: TenantCreate, request: Request, db: Session = Depends(get_db)):
    # only create self-record for current tenant context (solo: one row per tenant id)
    tenant_id = _tenant(request)
    existing = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if existing:
        return {"id": existing.id, "name": existing.name}
    tenant = Tenant(id=tenant_id, name=data.name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return {"id": tenant.id, "name": tenant.name}


@router.get("/")
@router.get("")
async def list_tenants(request: Request, db: Session = Depends(get_db)):
    tenant_id = _tenant(request)
    tenants = db.query(Tenant).filter(Tenant.id == tenant_id).all()
    return [{"id": t.id, "name": t.name} for t in tenants]


@router.get("/{tenant_id}")
async def get_tenant(tenant_id: str, request: Request, db: Session = Depends(get_db)):
    caller = _tenant(request)
    if tenant_id != caller:
        raise HTTPException(status_code=403, detail="Forbidden")
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": t.id, "name": t.name}
