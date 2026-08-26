from fastapi import APIRouter
import time

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])

waf_block_counter = 0
auth_failure_counter = 0
request_counter = 0
start_time = time.time()

@router.get("/security")
async def security_metrics():
    global waf_block_counter, auth_failure_counter, request_counter, start_time
    uptime_seconds = int(time.time() - start_time)
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    return [
        {"name": "WAF Blocks", "value": waf_block_counter, "status": "good"},
        {"name": "Active Threats", "value": 0, "status": "good"},
        {"name": "Auth Failures", "value": auth_failure_counter, "status": "good"},
        {"name": "Total Requests", "value": request_counter, "status": "good"},
        {"name": "Uptime", "value": f"{uptime_hours}h {uptime_minutes}m", "status": "good"}
    ]
