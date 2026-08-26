from fastapi import APIRouter, Request
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/audit", tags=["audit"])

AUDIT_LOGS = []

class AuditLogCreate(BaseModel):
    action: str
    resource: str
    resource_id: str = None
    data: dict = None

@router.post("/log")
async def create_audit_log(data: AuditLogCreate, request: Request):
    entry = {
        "id": str(uuid.uuid4()),
        "action": data.action,
        "resource": data.resource,
        "resource_id": data.resource_id,
        "data": data.data,
        "user_id": getattr(request.state, "user_id", "system"),
        "tenant_id": getattr(request.state, "tenant_id", "system"),
        "ip": request.client.host if request.client else "unknown",
        "timestamp": datetime.utcnow().isoformat()
    }
    AUDIT_LOGS.append(entry)
    return entry

@router.get("/")
async def get_audit_logs(limit: int = 100):
    return AUDIT_LOGS[-limit:]

@router.get("/{resource}/{resource_id}")
async def get_audit_logs_by_resource(resource: str, resource_id: str):
    return [l for l in AUDIT_LOGS if l["resource"] == resource and l["resource_id"] == resource_id]
