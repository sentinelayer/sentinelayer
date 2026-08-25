"""
Prometheus metrics untuk SentinelLayer
Section 7.17 - Observability
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from typing import Optional
import time

# ============ COUNTERS ============
# Total requests
requests_total = Counter(
    'sentinelayer_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'tenant', 'status_code']
)

# WAF blocks
waf_blocks_total = Counter(
    'sentinelayer_waf_blocks_total',
    'Total WAF blocked requests',
    ['endpoint', 'rule_id', 'severity']
)

# Rate limit hits
rate_limit_hits_total = Counter(
    'sentinelayer_rate_limit_hits_total',
    'Total rate limit hits',
    ['endpoint', 'dimension']
)

# Authentication failures
auth_failures_total = Counter(
    'sentinelayer_auth_failures_total',
    'Total authentication failures',
    ['reason']
)

# ============ HISTOGRAMS ============
# Request duration
request_duration = Histogram(
    'sentinelayer_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# ============ GAUGES ============
# Active requests
active_requests = Gauge(
    'sentinelayer_active_requests',
    'Active HTTP requests'
)

# WAF rules loaded
waf_rules_loaded = Gauge(
    'sentinelayer_waf_rules_loaded',
    'Number of WAF rules loaded'
)

# Tenants active
tenants_active = Gauge(
    'sentinelayer_tenants_active',
    'Number of active tenants'
)

# ============ Helper Functions ============

def record_request(method: str, endpoint: str, tenant: str, status_code: int, duration: float):
    """Record HTTP request metrics"""
    requests_total.labels(
        method=method,
        endpoint=endpoint,
        tenant=tenant or 'unknown',
        status_code=str(status_code)
    ).inc()
    
    request_duration.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)

def record_waf_block(endpoint: str, rule_id: str, severity: str):
    """Record WAF block"""
    waf_blocks_total.labels(
        endpoint=endpoint,
        rule_id=rule_id,
        severity=severity
    ).inc()

def record_rate_limit_hit(endpoint: str, dimension: str):
    """Record rate limit hit"""
    rate_limit_hits_total.labels(
        endpoint=endpoint,
        dimension=dimension
    ).inc()

def record_auth_failure(reason: str):
    """Record authentication failure"""
    auth_failures_total.labels(reason=reason).inc()

def increment_active_requests():
    """Increment active requests counter"""
    active_requests.inc()

def decrement_active_requests():
    """Decrement active requests counter"""
    active_requests.dec()

def set_waf_rules_count(count: int):
    """Set WAF rules count"""
    waf_rules_loaded.set(count)

def set_tenants_active(count: int):
    """Set active tenants count"""
    tenants_active.set(count)

def get_metrics():
    """Get all metrics in Prometheus format"""
    return generate_latest(REGISTRY)

# ============ Middleware for FastAPI ============

from fastapi import Request, Response
import time

async def metrics_middleware(request: Request, call_next):
    """FastAPI middleware untuk metrics"""
    
    # Increment active requests
    increment_active_requests()
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
    except Exception as e:
        # Record error
        duration = time.time() - start_time
        record_request(
            method=request.method,
            endpoint=request.url.path,
            tenant=getattr(request.state, 'tenant_id', 'unknown'),
            status_code=500,
            duration=duration
        )
        decrement_active_requests()
        raise e
    
    duration = time.time() - start_time
    
    # Record request metrics
    record_request(
        method=request.method,
        endpoint=request.url.path,
        tenant=getattr(request.state, 'tenant_id', 'unknown'),
        status_code=response.status_code,
        duration=duration
    )
    
    decrement_active_requests()
    return response
