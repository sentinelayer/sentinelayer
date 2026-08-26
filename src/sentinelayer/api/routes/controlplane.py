from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.sentinelayer.database import get_db
from src.sentinelayer.database.models import Tenant, Application, Policy
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

@router.post("/applications")
async def create_application(tenant_id: str, name: str, db: Session = Depends(get_db)):
    app = Application(id=str(uuid.uuid4()), tenant_id=tenant_id, name=name)
    db.add(app)
    db.commit()
    db.refresh(app)
    return {"id": app.id, "name": app.name}

@router.get("/applications")
async def list_applications(tenant_id: str = None, db: Session = Depends(get_db)):
    query = db.query(Application)
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    return [{"id": a.id, "name": a.name, "tenant_id": a.tenant_id} for a in query.all()]
