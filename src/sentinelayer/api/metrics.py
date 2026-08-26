from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])

waf_block_counter = 0
auth_failure_counter = 0

@router.get("/security")
async def security_metrics():
    global waf_block_counter, auth_failure_counter
    return [
        {"name": "WAF Blocks", "value": waf_block_counter, "status": "good"},
        {"name": "Active Threats", "value": 0, "status": "good"},
        {"name": "Auth Failures", "value": auth_failure_counter, "status": "good"},
        {"name": "Risk Score", "value": 0, "status": "good"}
    ]
