from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/admin/high-risk-actions", tags=["admin"])

class HighRiskAction(BaseModel):
    action: str
    reason: str

ACTIONS = []

@router.post("/")
async def execute_high_risk_action(data: HighRiskAction):
    if data.action not in ["block_tenant", "revoke_all_tokens", "disable_waf", "force_rotation"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    result = {
        "id": str(uuid.uuid4()),
        "action": data.action,
        "reason": data.reason,
        "status": "pending_approval",
        "executed_at": datetime.utcnow().isoformat(),
        "requires_approval": True
    }
    ACTIONS.append(result)
    return result

@router.get("/")
async def list_high_risk_actions():
    return ACTIONS

@router.post("/{id}/approve")
async def approve_high_risk_action(id: str):
    for a in ACTIONS:
        if a["id"] == id:
            a["status"] = "approved"
            a["approved_at"] = datetime.utcnow().isoformat()
            return a
    return {"error": "Action not found"}

@router.post("/{id}/reject")
async def reject_high_risk_action(id: str):
    for a in ACTIONS:
        if a["id"] == id:
            a["status"] = "rejected"
            a["rejected_at"] = datetime.utcnow().isoformat()
            return a
    return {"error": "Action not found"}
