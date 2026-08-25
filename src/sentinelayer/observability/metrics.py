from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
import time
from fastapi import Request

requests_total = Counter(
    'sentinelayer_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'tenant', 'status_code']
)

waf_blocks_total = Counter(
    'sentinelayer_waf_blocks_total',
    'Total WAF blocked requests',
    ['endpoint', 'rule_id', 'severity']
)

def record_request(method, endpoint, tenant, status_code, duration):
    try:
        requests_total.labels(
            method=method or 'unknown',
            endpoint=endpoint or 'unknown',
            tenant=tenant or 'unknown',
            status_code=str(status_code) if status_code else '0'
        ).inc()
    except Exception as e:
        print(f"Metrics error: {e}")

def get_metrics():
    try:
        return generate_latest(REGISTRY)
    except Exception as e:
        return f"Error: {e}".encode()

async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    record_request(
        method=request.method,
        endpoint=request.url.path,
        tenant=getattr(request.state, 'tenant_id', 'unknown'),
        status_code=response.status_code,
        duration=duration
    )
    return response
