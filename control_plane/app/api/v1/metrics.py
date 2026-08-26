from fastapi import APIRouter
import time

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])

start_time = time.time()

@router.get("/security")
async def security_metrics():
    uptime = int(time.time() - start_time)
    return [
        {"name": "WAF Blocks", "value": 0, "status": "good"},
        {"name": "Active Threats", "value": 0, "status": "good"},
        {"name": "Auth Failures", "value": 0, "status": "good"},
        {"name": "Uptime", "value": f"{uptime}s", "status": "good"}
    ]
