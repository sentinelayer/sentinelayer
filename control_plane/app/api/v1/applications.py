from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from control_plane.app.infrastructure.db.session import get_db
from control_plane.app.domain.application.entity import Application
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/applications", tags=["applications"])

class AppCreate(BaseModel):
    name: str
    tenant_id: str

@router.post("/")
async def create_application(data: AppCreate, db: Session = Depends(get_db)):
    app = Application(id=str(uuid.uuid4()), name=data.name, tenant_id=data.tenant_id)
    db.add(app)
    db.commit()
    db.refresh(app)
    return {"id": app.id, "name": app.name, "tenant_id": app.tenant_id}

@router.get("/")
async def list_applications(tenant_id: str = None, db: Session = Depends(get_db)):
    query = db.query(Application)
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    apps = query.all()
    return [{"id": a.id, "name": a.name, "tenant_id": a.tenant_id} for a in apps]
