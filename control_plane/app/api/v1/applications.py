from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import Application
from pydantic import BaseModel
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationCreate(BaseModel):
    name: str
    environment: str = "production"


@router.post("/")
@router.post("")
async def create_application(
    data: ApplicationCreate,
    request: Request,
    db: Session = Depends(db_with_tenant),
):
    tid = tenant_id(request)
    app = Application(
        id=str(uuid.uuid4()),
        name=data.name,
        tenant_id=tid,
        created_at=datetime.now(timezone.utc),
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return {"id": app.id, "name": app.name, "tenant_id": tid, "environment": data.environment}


@router.get("/")
@router.get("")
async def list_applications(request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    apps = db.query(Application).filter(Application.tenant_id == tid).all()
    return [{"id": a.id, "name": a.name, "tenant_id": a.tenant_id} for a in apps]


@router.get("/{app_id}")
async def get_application(app_id: str, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    app = db.query(Application).filter(Application.id == app_id, Application.tenant_id == tid).first()
    if not app:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": app.id, "name": app.name, "tenant_id": app.tenant_id}
