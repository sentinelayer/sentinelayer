from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from control_plane.app.api.deps import db_with_tenant, tenant_id
from control_plane.app.infrastructure.db.models import Incident
from pydantic import BaseModel
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/incidents", tags=["incidents"])


class IncidentCreate(BaseModel):
    severity: str
    description: str


@router.post("/")
@router.post("")
async def create_incident(data: IncidentCreate, request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    incident = Incident(
        id=str(uuid.uuid4()),
        severity=data.severity,
        description=data.description,
        tenant_id=tid,
        status="open",
        created_at=datetime.now(timezone.utc),
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return {"id": incident.id, "severity": incident.severity, "status": incident.status, "tenant_id": tid}


@router.get("/")
@router.get("")
async def list_incidents(request: Request, db: Session = Depends(db_with_tenant)):
    tid = tenant_id(request)
    incidents = db.query(Incident).filter(Incident.tenant_id == tid).all()
    return [{"id": i.id, "severity": i.severity, "status": i.status, "tenant_id": i.tenant_id} for i in incidents]
