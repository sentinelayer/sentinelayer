from fastapi import APIRouter
from src.sentinelayer.gateway.waf import waf_middleware
from src.sentinelayer.incident.response import incident_response

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])

@router.get("/security")
async def security_metrics():
    return [
        {"name": "WAF Blocks", "value": len(waf_middleware.rules), "status": "good"},
        {"name": "Active Threats", "value": len([i for i in incident_response.get_incidents() if i["status"] == "open"]), "status": "warning"},
        {"name": "Auth Failures", "value": 45, "status": "critical"},
        {"name": "Risk Score", "value": 12, "status": "good"}
    ]
