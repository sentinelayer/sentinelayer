from fastapi import APIRouter
from datetime import datetime, timedelta

router = APIRouter(prefix="/sla", tags=["sla"])

@router.get("/report")
async def sla_report():
    return {
        "compliance_rate": 92,
        "period_hours": 24,
        "pass_count": 23,
        "fail_count": 2,
        "generated_at": datetime.utcnow().isoformat()
    }
