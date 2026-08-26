from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from control_plane.app.infrastructure.db.session import get_db
from control_plane.app.infrastructure.db.models import Application
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/applications", tags=["applications"])


class AppCreate(BaseModel):
    name: str
    environment: str = "production"


def _tenant(request: Request) -> str:
    tid = getattr(request.state, "tenant_id", None)
    if not tid:
        raise HTTPException(status_code=400, detail="Missing tenant ID")
    return tid


@router.post("/")
@router.post("")
async def create_application(data: AppCreate, request: Request, db: Session = Depends(get_db)):
    tenant_id = _tenant(request)
    app = Application(id=str(uuid.uuid4()), name=data.name, tenant_id=tenant_id)
    db.add(app)
    db.commit()
    db.refresh(app)
    return {"id": app.id, "name": app.name, "tenant_id": app.tenant_id, "environment": data.environment}


@router.get("/")
@router.get("")
async def list_applications(request: Request, db: Session = Depends(get_db)):
    tenant_id = _tenant(request)
    apps = db.query(Application).filter(Application.tenant_id == tenant_id).all()
    return [{"id": a.id, "name": a.name, "tenant_id": a.tenant_id} for a in apps]


@router.get("/{app_id}")
async def get_application(app_id: str, request: Request, db: Session = Depends(get_db)):
    tenant_id = _tenant(request)
    app = db.query(Application).filter(Application.id == app_id, Application.tenant_id == tenant_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": app.id, "name": app.name, "tenant_id": app.tenant_id}
