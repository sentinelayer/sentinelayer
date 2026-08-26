from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.sentinelayer.api import auth
from src.sentinelayer.api import frontend
from src.sentinelayer.gateway.waf import waf_middleware
from src.sentinelayer.gateway.ssrf import ssrf_middleware
from src.sentinelayer.gateway.threatintel import threat_intel
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
app.include_router(frontend.router)

@app.middleware("http")
async def security_pipeline(request: Request, call_next):
    # 1. WAF check
    waf_result = await waf_middleware.process(request, call_next)
    if hasattr(waf_result, "status_code") and waf_result.status_code == 403:
        return waf_result
    
    # 2. SSRF check
    ssrf_result = await ssrf_middleware.process(request, call_next)
    if hasattr(ssrf_result, "status_code") and ssrf_result.status_code == 403:
        return ssrf_result
    
    # 3. Threat Intel check (for IP)
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
