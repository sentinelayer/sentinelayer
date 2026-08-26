from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from control_plane.app.infrastructure.db.session import get_db
from control_plane.app.domain.incident.entity import Incident
from pydantic import BaseModel
import uuid
from datetime import datetime

router = APIRouter(prefix="/incidents", tags=["incidents"])

class IncidentCreate(BaseModel):
    severity: str
    description: str
    tenant_id: str

@router.post("/")
async def create_incident(data: IncidentCreate, db: Session = Depends(get_db)):
    incident = Incident(
        id=str(uuid.uuid4()),
        severity=data.severity,
        description=data.description,
        tenant_id=data.tenant_id,
        status="open",
        created_at=datetime.utcnow().isoformat()
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return {"id": incident.id, "status": incident.status}

@router.get("/")
async def list_incidents(tenant_id: str = None, db: Session = Depends(get_db)):
    query = db.query(Incident)
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    incidents = query.all()
    return [{"id": i.id, "severity": i.severity, "status": i.status} for i in incidents]
