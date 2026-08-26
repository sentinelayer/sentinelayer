from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])

@router.get("/security")
async def security_metrics():
    return [
        {"name": "WAF Blocks", "value": 0, "status": "good"},
        {"name": "Active Threats", "value": 0, "status": "good"},
        {"name": "Auth Failures", "value": 0, "status": "good"},
        {"name": "Risk Score", "value": 0, "status": "good"}
    ]
