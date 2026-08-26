from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from control_plane.app.infrastructure.db.session import get_db
from control_plane.app.infrastructure.db.models import Evidence
from pydantic import BaseModel
import uuid
from datetime import datetime

router = APIRouter(prefix="/evidence", tags=["evidence"])

class EvidenceCreate(BaseModel):
    artifact: str
    requirement_id: str
    control_id: str

@router.post("/")
async def create_evidence(data: EvidenceCreate, db: Session = Depends(get_db)):
    evidence = Evidence(
        id=str(uuid.uuid4()),
        artifact=data.artifact,
        requirement_id=data.requirement_id,
        control_id=data.control_id,
        status="CREATED",
        created_at=datetime.utcnow()
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return {"id": evidence.id, "artifact": evidence.artifact, "status": evidence.status}

@router.get("/")
async def list_evidence(db: Session = Depends(get_db)):
    evidences = db.query(Evidence).all()
    return [{"id": e.id, "artifact": e.artifact, "status": e.status} for e in evidences]

@router.get("/{id}")
async def get_evidence(id: str, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter_by(id=id).first()
    if not evidence:
        return {"error": "Evidence not found"}
    return {"id": evidence.id, "artifact": evidence.artifact, "status": evidence.status}
