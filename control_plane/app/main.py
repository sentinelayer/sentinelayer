from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from control_plane.app.api.v1 import auth, metrics, health
from control_plane.app.middleware.tenant import TenantMiddleware
from control_plane.app.middleware.security_headers import SecurityHeadersMiddleware
from control_plane.app.middleware.ratelimit import RateLimitMiddleware

app = FastAPI(title="SentinelLayer Control Plane", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TenantMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(auth.router)
app.include_router(metrics.router)
app.include_router(health.router)

@app.get("/")
async def root():
    return {"status": "ok", "service": "SentinelLayer Control Plane"}
