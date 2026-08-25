from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from typing import Optional
import time
import logging

logger = logging.getLogger(__name__)

# ============ COUNTERS ============
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

rate_limit_hits_total = Counter(
    'sentinelayer_rate_limit_hits_total',
    'Total rate limit hits',
    ['endpoint', 'dimension']
)

auth_failures_total = Counter(
    'sentinelayer_auth_failures_total',
    'Total authentication failures',
    ['reason']
)

# ============ HISTOGRAMS ============
request_duration = Histogram(
    'sentinelayer_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# ============ GAUGES ============
active_requests = Gauge(
    'sentinelayer_active_requests',
    'Active HTTP requests'
)

waf_rules_loaded = Gauge(
    'sentinelayer_waf_rules_loaded',
    'Number of WAF rules loaded'
)

tenants_active = Gauge(
    'sentinelayer_tenants_active',
    'Number of active tenants'
)

# ============ RECORD FUNCTIONS ============
def record_request(method: str, endpoint: str, tenant: str, status_code: int, duration: float):
    try:
        requests_total.labels(
            method=method or 'unknown',
            endpoint=endpoint or 'unknown',
            tenant=tenant or 'unknown',
            status_code=str(status_code) if status_code else '0'
        ).inc()
        request_duration.labels(
            method=method or 'unknown',
            endpoint=endpoint or 'unknown'
        ).observe(duration)
    except Exception as e:
        logger.error(f"Metrics error: {e}")

def record_waf_block(endpoint: str, rule_id: str, severity: str):
    try:
        waf_blocks_total.labels(
            endpoint=endpoint or 'unknown',
            rule_id=rule_id or 'unknown',
            severity=severity or 'unknown'
        ).inc()
    except Exception as e:
        logger.error(f"Metrics error: {e}")

def record_rate_limit_hit(endpoint: str, dimension: str):
    try:
        rate_limit_hits_total.labels(
            endpoint=endpoint or 'unknown',
            dimension=dimension or 'unknown'
        ).inc()
    except Exception as e:
        logger.error(f"Metrics error: {e}")

def record_auth_failure(reason: str):
    try:
        auth_failures_total.labels(reason=reason or 'unknown').inc()
    except Exception as e:
        logger.error(f"Metrics error: {e}")

def increment_active_requests():
    active_requests.inc()

def decrement_active_requests():
    active_requests.dec()

def set_waf_rules_count(count: int):
    waf_rules_loaded.set(count)

def get_metrics():
    try:
        return generate_latest(REGISTRY)
    except Exception as e:
        return f"Error generating metrics: {e}".encode()
