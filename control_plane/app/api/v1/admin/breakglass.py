from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from control_plane.app.infrastructure.db.session import get_db
from control_plane.app.domain.breakglass.entity import BreakGlass
import uuid
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin/breakglass", tags=["admin"])

@router.post("/")
async def create_breakglass(user_id: str, reason: str, db: Session = Depends(get_db)):
    bg = BreakGlass(
        id=str(uuid.uuid4()),
        user_id=user_id,
        reason=reason,
        status="PENDING",
        expires_at=(datetime.utcnow() + timedelta(hours=1)).isoformat()
    )
    db.add(bg)
    db.commit()
    db.refresh(bg)
    return {"id": bg.id, "status": bg.status}

@router.get("/")
async def list_breakglass(db: Session = Depends(get_db)):
    bgs = db.query(BreakGlass).filter_by(status="PENDING").all()
    return [{"id": bg.id, "user_id": bg.user_id, "reason": bg.reason} for bg in bgs]
