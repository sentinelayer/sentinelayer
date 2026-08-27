import os

from fastapi import FastAPI, Header, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST
from fastapi.middleware.cors import CORSMiddleware

from control_plane.app.api.v1.router import router
from control_plane.app.lifespan import lifespan
from control_plane.app.infrastructure.observability.metrics import MetricsMiddleware, get_metrics
from control_plane.app.middleware.auth import AuthMiddleware
from control_plane.app.middleware.rbac import RBACMiddleware
from control_plane.app.middleware.tenant import TenantMiddleware

app = FastAPI(title="SentinelLayer Control Plane", version="0.1.0", lifespan=lifespan)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware from inner to outer: authentication must populate claims
# before tenant and RBAC checks run.
app.add_middleware(MetricsMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(RBACMiddleware)
app.add_middleware(AuthMiddleware)

app.include_router(router, prefix="/api/v1")


@app.get("/metrics")
async def metrics_endpoint(x_metrics_token: str | None = Header(default=None)):
    expected = os.getenv("METRICS_TOKEN")
    if os.getenv("SL_ENV", "development").lower() == "production" and not expected:
        raise HTTPException(status_code=503, detail="METRICS_TOKEN is required in production")
    if expected and x_metrics_token != expected:
        raise HTTPException(status_code=401, detail="Invalid metrics token")
    return Response(content=get_metrics(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    return {"status": "ok", "service": "SentinelLayer Control Plane"}


@app.get("/health")
async def root_health():
    return {"status": "healthy", "service": "control-plane"}
