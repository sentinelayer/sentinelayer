from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from sentinelayer.api.routes import auth, orders  # ✅ routes BUKAN routers
from sentinelayer.api.middleware.auth import AuthMiddleware
from sentinelayer.api.middleware.ratelimit import RateLimitMiddleware
from sentinelayer.api.middleware.tenant import TenantMiddleware
from sentinelayer.api.middleware.waf import WAFMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SentinelLayer API",
    description="Security control and enforcement platform (Blueprint 10/10)",
    version="0.1.0",
    docs_url="/docs"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init middlewares (order matters!)
waf_middleware = WAFMiddleware()
auth_middleware = AuthMiddleware()
rate_limit_middleware = RateLimitMiddleware()
tenant_middleware = TenantMiddleware()

# Security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    public_paths = ["/", "/health", "/docs", "/redoc", "/openapi.json", "/api/v1/auth/login"]
    
    # 1. WAF (all requests)
    if request.url.path not in public_paths:
        await waf_middleware(request)
    
    # 2. Rate limit
    if request.url.path not in public_paths:
        await rate_limit_middleware(request)
    
    # 3. Auth
    if request.url.path not in public_paths:
        await auth_middleware(request)
    
    # 4. Tenant isolation
    if request.url.path not in public_paths:
        await tenant_middleware(request)
    
    # Process request
    start_time = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time() - start_time)
    
    # Add WAF headers
    if hasattr(request.state, "waf_violations"):
        response.headers["X-WAF-Violations"] = str(request.state.waf_violations)
        response.headers["X-WAF-Severity"] = request.state.waf_severity
    
    return response

@app.get("/")
async def root():
    return {
        "service": "SentinelLayer",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "security": {
            "jwt": "enabled",
            "rate_limit": "enabled",
            "tenant_isolation": "enabled",
            "bola_protection": "enabled",
            "waf": "enabled"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "path": request.url.path}
    )
