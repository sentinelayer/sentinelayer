from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.sentinelayer.database import get_db
from src.sentinelayer.database.models import Tenant
import uuid

router = APIRouter(prefix="/api/v1/controlplane", tags=["controlplane"])

@router.post("/tenants")
async def create_tenant(name: str, db: Session = Depends(get_db)):
    tenant = Tenant(id=str(uuid.uuid4()), name=name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return {"id": tenant.id, "name": tenant.name}

@router.get("/tenants")
async def list_tenants(db: Session = Depends(get_db)):
    return [{"id": t.id, "name": t.name} for t in db.query(Tenant).all()]
