from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
import time
from fastapi import Request

requests_total = Counter('sentinelayer_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('sentinelayer_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
active_requests = Gauge('sentinelayer_active_requests', 'Active requests')
waf_blocks = Counter('sentinelayer_waf_blocks_total', 'WAF blocked requests', ['rule_id'])

def record_request(method: str, endpoint: str, status: int, duration: float):
    requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    request_duration.labels(method=method, endpoint=endpoint).observe(duration)

def get_metrics():
    return generate_latest(REGISTRY)

async def metrics_middleware(request: Request, call_next):
    active_requests.inc()
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    record_request(request.method, request.url.path, response.status_code, duration)
    active_requests.dec()
    return response
