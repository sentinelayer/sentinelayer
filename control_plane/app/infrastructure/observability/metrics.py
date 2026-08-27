from __future__ import annotations

import re
import time

from fastapi import Request
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"])
ACTIVE_REQUESTS = Gauge("http_requests_active", "Active HTTP requests")
WAF_BLOCKS = Counter("waf_blocks_total", "Total WAF blocks")
AUTH_FAILURES = Counter("auth_failures_total", "Total authentication failures")
RISK_SCORE = Gauge("risk_score_current", "Current risk score")

_UUID = re.compile(r"/[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}/")
_LONG_ID = re.compile(r"/\d{2,}/")


def metric_endpoint(request: Request) -> str:
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    if template and len(template) <= 160:
        return template
    path = request.url.path
    path = _UUID.sub("/{id}/", path)
    path = _LONG_ID.sub("/{id}/", path)
    return path[:160] or "/"


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        endpoint = metric_endpoint(request)
        ACTIVE_REQUESTS.inc()
        start = time.monotonic()
        try:
            response = await call_next(request)
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(response.status_code)).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.monotonic() - start)
            return response
        except Exception:
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status="500").inc()
            raise
        finally:
            ACTIVE_REQUESTS.dec()


def get_metrics():
    return generate_latest()
