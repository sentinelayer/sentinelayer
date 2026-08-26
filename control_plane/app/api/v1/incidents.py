from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from control_plane.app.infrastructure.db.session import get_db
from control_plane.app.infrastructure.db.models import Incident
from pydantic import BaseModel
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/incidents", tags=["incidents"])


class IncidentCreate(BaseModel):
    severity: str
    description: str


def _tenant(request: Request) -> str:
    tid = getattr(request.state, "tenant_id", None)
    if not tid:
        raise HTTPException(status_code=400, detail="Missing tenant ID")
    return tid


@router.post("/")
@router.post("")
async def create_incident(data: IncidentCreate, request: Request, db: Session = Depends(get_db)):
    tenant_id = _tenant(request)
    incident = Incident(
        id=str(uuid.uuid4()),
        severity=data.severity,
        description=data.description,
        tenant_id=tenant_id,
        status="open",
        created_at=datetime.now(timezone.utc),
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return {"id": incident.id, "severity": incident.severity, "status": incident.status, "tenant_id": tenant_id}


@router.get("/")
@router.get("")
async def list_incidents(request: Request, db: Session = Depends(get_db)):
    tenant_id = _tenant(request)
    incidents = db.query(Incident).filter(Incident.tenant_id == tenant_id).all()
    return [{"id": i.id, "severity": i.severity, "status": i.status, "tenant_id": i.tenant_id} for i in incidents]
