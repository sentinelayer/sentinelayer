from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from control_plane.app.infrastructure.db.session import get_db
from control_plane.app.domain.tenant.entity import Tenant
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/tenants", tags=["tenants"])

class TenantCreate(BaseModel):
    name: str

@router.post("/")
async def create_tenant(data: TenantCreate, db: Session = Depends(get_db)):
    tenant = Tenant(id=str(uuid.uuid4()), name=data.name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return {"id": tenant.id, "name": tenant.name}

@router.get("/")
async def list_tenants(db: Session = Depends(get_db)):
    tenants = db.query(Tenant).all()
    return [{"id": t.id, "name": t.name} for t in tenants]
