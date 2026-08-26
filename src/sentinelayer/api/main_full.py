from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.sentinelayer.api import auth
from src.sentinelayer.gateway.waf import waf_middleware
from src.sentinelayer.gateway.ssrf import ssrf_middleware
from src.sentinelayer.database import engine
from src.sentinelayer.database.models import Base
import os

app = FastAPI(title="SentinelLayer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)

@app.middleware("http")
async def waf_and_ssrf_middleware(request, call_next):
    waf_result = await waf_middleware.process(request, call_next)
    if hasattr(waf_result, "status_code") and waf_result.status_code == 403:
        return waf_result
    return await ssrf_middleware.process(request, call_next)

@app.get("/")
async def root():
    return {
        "service": "SentinelLayer",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "auth": "/api/v1/auth",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "testing": False
    }

@app.get("/metrics")
async def metrics():
    return {"status": "metrics endpoint"}
