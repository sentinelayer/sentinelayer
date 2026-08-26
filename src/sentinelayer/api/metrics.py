from fastapi import APIRouter, Request
from src.sentinelayer.incident.response import incident_response
from src.sentinelayer.risk.engine import risk_engine
import time

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])

waf_block_counter = 0
auth_failure_counter = 0
request_counter = 0
start_time = time.time()

def increment_waf_block():
    global waf_block_counter
    waf_block_counter += 1

def increment_auth_failure():
    global auth_failure_counter
    auth_failure_counter += 1

def increment_request():
    global request_counter
    request_counter += 1

@router.get("/security")
async def security_metrics(request: Request):
    global waf_block_counter, auth_failure_counter, request_counter, start_time

    uptime_seconds = int(time.time() - start_time)
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60

    active_incidents = len([i for i in incident_response.get_incidents() if i["status"] == "open"])
    total_incidents = len(incident_response.get_incidents())

    # Hitung risk score dari context saat ini
    sample_context = {
        "failed_attempts": auth_failure_counter,
        "suspicious_ip": False,
        "unusual_time": False,
        "multiple_tenants": False
    }
    risk_score = risk_engine.calculate(sample_context)

    return [
        {"name": "WAF Blocks", "value": waf_block_counter, "status": "good"},
        {"name": "Active Threats", "value": active_incidents, "status": "warning" if active_incidents > 0 else "good"},
        {"name": "Auth Failures", "value": auth_failure_counter, "status": "critical" if auth_failure_counter > 100 else "good"},
        {"name": "Risk Score", "value": risk_score, "status": "good" if risk_score < 30 else "warning" if risk_score < 60 else "critical"},
        {"name": "Total Incidents", "value": total_incidents, "status": "good"},
        {"name": "Total Requests", "value": request_counter, "status": "good"},
        {"name": "Uptime", "value": f"{uptime_hours}h {uptime_minutes}m", "status": "good"}
    ]

@router.get("/waf")
async def waf_metrics():
    from src.sentinelayer.gateway.waf import waf_middleware
    return {
        "total_rules": len(waf_middleware.rules),
        "blocks": waf_block_counter,
        "status": "active"
    }

@router.get("/incidents")
async def incident_metrics():
    incidents = incident_response.get_incidents()
    return {
        "total": len(incidents),
        "open": len([i for i in incidents if i["status"] == "open"]),
        "resolved": len([i for i in incidents if i["status"] == "resolved"])
    }
