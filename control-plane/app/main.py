from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.sentinelayer.api import auth, health, metrics
from src.sentinelayer.api.routes import controlplane
from src.sentinelayer.api.middleware.security_headers import SecurityHeadersMiddleware
from src.sentinelayer.api.middleware.ratelimit import RateLimitMiddleware
from src.sentinelayer.gateway.ssrf import SSRFMiddleware
import os

app = FastAPI(title="SentinelLayer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SSRFMiddleware)

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(controlplane.router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "SentinelLayer API is running"}

@app.get("/metrics")
async def metrics_endpoint():
    return {"status": "metrics endpoint"}
