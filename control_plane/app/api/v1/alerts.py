import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/alerts", tags=["alerts"])

class AlertCreate(BaseModel):
    severity: str
    message: str
    source: str = "system"

ALERTS = []

@router.post("/")
async def create_alert(data: AlertCreate):
    alert = {
        "id": str(uuid.uuid4()),
        "severity": data.severity,
        "message": data.message,
        "source": data.source,
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    ALERTS.append(alert)
    return alert

@router.get("/")
async def list_alerts(status: str = None):
    if status:
        return [a for a in ALERTS if a["status"] == status]
    return ALERTS

@router.post("/{id}/resolve")
async def resolve_alert(id: str):
    for a in ALERTS:
        if a["id"] == id:
            a["status"] = "resolved"
            a["resolved_at"] = datetime.utcnow().isoformat()
            return a
    return {"error": "Alert not found"}
