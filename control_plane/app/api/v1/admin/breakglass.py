from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from control_plane.app.infrastructure.db.session import get_db
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin/breakglass", tags=["admin"])

class BreakGlassCreate(BaseModel):
    user_id: str
    reason: str

@router.post("/")
async def create_breakglass(data: BreakGlassCreate, db: Session = Depends(get_db)):
    return {
        "id": str(uuid.uuid4()),
        "user_id": data.user_id,
        "reason": data.reason,
        "status": "PENDING",
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }

@router.get("/")
async def list_breakglass(db: Session = Depends(get_db)):
    return []
