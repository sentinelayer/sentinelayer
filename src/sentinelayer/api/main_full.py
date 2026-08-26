from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.sentinelayer.api import auth, health, metrics
from src.sentinelayer.api.routes import controlplane
from src.sentinelayer.gateway.waf import waf_middleware
from src.sentinelayer.gateway.ssrf import SSRFMiddleware
from src.sentinelayer.gateway.threatintel import threat_intel
from src.sentinelayer.api.middleware.auth import AuthMiddleware
from src.sentinelayer.api.middleware.tenant import TenantMiddleware
from src.sentinelayer.api.middleware.ratelimit import RateLimitMiddleware
from src.sentinelayer.api.middleware.pipeline import SecurityPipelineMiddleware
from src.sentinelayer.api.middleware.security_headers import SecurityHeadersMiddleware
from src.sentinelayer.observability.metrics import MetricsMiddleware
from src.sentinelayer.database import engine
from src.sentinelayer.database.models import Base
from src.sentinelayer.security.provenance import provenance
import os

app = FastAPI(title="SentinelLayer API", version="0.1.0")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://sentinelayer.up.railway.app").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
)

app.add_middleware(MetricsMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, calls_per_minute=int(os.getenv("RATE_LIMIT", "60")))
app.add_middleware(TenantMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(SSRFMiddleware)
app.add_middleware(SecurityPipelineMiddleware)

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(controlplane.router)

@app.middleware("http")
async def waf_and_threat(request: Request, call_next):
    waf_result = await waf_middleware.process(request, call_next)
    if hasattr(waf_result, "status_code") and waf_result.status_code == 403:
        return waf_result

    client_ip = request.client.host if request.client else "unknown"
    if client_ip != "unknown":
        threat_result = await threat_intel.check_ip(client_ip)
        if threat_result.get("malicious"):
            return JSONResponse(
                status_code=403,
                content={"error": "Blocked by Threat Intelligence", "source": threat_result.get("source")}
            )

    return await call_next(request)

@app.get("/")
async def root():
    status = "operational" if provenance.verified else "degraded"
    return {
        "service": "SentinelLayer",
        "version": "0.1.0",
        "status": status,
        "docs": "/docs",
        "auth": "/api/v1/auth",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "testing": False,
        "provenance_verified": provenance.verified
    }

@app.get("/metrics")
async def prometheus_metrics():
    from src.sentinelayer.observability.metrics import get_metrics
    return Response(content=get_metrics(), media_type="text/plain")
