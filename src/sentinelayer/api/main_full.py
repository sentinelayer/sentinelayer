import os
import time
import logging
import uuid
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

from sentinelayer.api.routes import auth
from sentinelayer.database.models.base import DatabaseManager
from sentinelayer.database.models.order import OrderRepository, OrderStatus
from sentinelayer.backend.internal.auth.authorization import AuthorizationMiddleware, Resource

# ============ MIDDLEWARE ============
from sentinelayer.api.middleware.auth import AuthMiddleware
from sentinelayer.api.middleware.waf import WAFMiddleware
from sentinelayer.api.middleware.ratelimit import RateLimitMiddleware
from sentinelayer.api.middleware.tenant import TenantMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ ENVIRONMENT ============
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
TESTING = os.getenv("TESTING", "false").lower() == "true"

if TESTING and ENVIRONMENT == "production":
    raise RuntimeError("❌ TESTING mode is NOT allowed in production environment!")

if TESTING:
    logger.warning("⚠️ RUNNING IN TESTING MODE - AUTH DISABLED")

# ============ CORS ============
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# ============ DATABASE ============
db_manager = DatabaseManager()
db_manager.create_tables()

# ============ FASTAPI APP ============
app = FastAPI(
    title="SentinelLayer API",
    description="Security control and enforcement platform",
    version="0.1.0",
    docs_url="/docs"
)

# ============ CORS ============
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    max_age=86400,
)

# ============ INIT MIDDLEWARE ============
auth_middleware = AuthMiddleware()
waf_middleware = WAFMiddleware()
rate_limit_middleware = RateLimitMiddleware()
tenant_middleware = TenantMiddleware()
bola_middleware = AuthorizationMiddleware()

# ============ GLOBAL SECURITY MIDDLEWARE ============
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    public_paths = ["/", "/health", "/docs", "/redoc", "/openapi.json", "/metrics", "/api/v1/auth/login"]
    
    if TESTING:
        if request.url.path not in public_paths:
            await waf_middleware(request)
            await rate_limit_middleware(request)
        response = await call_next(request)
        return response
    
    if request.url.path not in public_paths:
        await waf_middleware(request)
        await rate_limit_middleware(request)
        await auth_middleware(request)
        await tenant_middleware(request)
    
    response = await call_next(request)
    return response

# ============ DEPENDENCY ============
async def get_current_user(request: Request):
    if TESTING:
        return {"sub": "test-user", "tenant_id": "tenant-test", "roles": ["user"]}
    user = getattr(request.state, 'user', None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# ============ MODELS ============
class OrderCreate(BaseModel):
    product_id: str
    quantity: int
    total_amount: float

class OrderResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    quantity: int
    total_amount: float
    status: str
    tenant_id: str
    created_at: str
    updated_at: str

# ============ ROOT ============
@app.get("/")
async def root():
    return {
        "service": "SentinelLayer",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "auth": "/api/v1/auth",
        "environment": ENVIRONMENT,
        "testing": TESTING
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/metrics")
async def metrics():
    return {"message": "Metrics endpoint"}

# ============ BOLA CHECK ============
def check_bola_order(order_id: str, tenant_id: str, user_id: str, roles: list = None):
    repo = OrderRepository(db_manager, tenant_id)
    order = repo.get_order(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    resource = Resource(
        type="order",
        id=order_id,
        tenant_id=order.tenant_id,
        owner_id=order.user_id
    )
    
    allowed, reason = bola_middleware.validate_request(
        resource=resource,
        user_tenant_id=tenant_id,
        user_id=user_id,
        user_roles=roles
    )
    
    if not allowed:
        logger.warning(f"BOLA block: {reason} - order={order_id}, user={user_id}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    return order

# ============ ORDERS ============
@app.post("/api/v1/orders/", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    tenant_id = current_user.get("tenant_id", "tenant-default")
    user_id = current_user.get("sub", "user-default")
    
    repo = OrderRepository(db_manager, tenant_id)
    order_data = {
        "user_id": user_id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "total_amount": order.total_amount,
        "created_by": user_id,
        "status": OrderStatus.PENDING
    }
    created = repo.create_order(order_data)
    return OrderResponse(**created.to_dict())

@app.get("/api/v1/orders/", response_model=List[OrderResponse])
async def list_orders(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    tenant_id = current_user.get("tenant_id", "tenant-default")
    repo = OrderRepository(db_manager, tenant_id)
    orders = repo.get_all_orders()
    return [OrderResponse(**order.to_dict()) for order in orders]

@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    tenant_id = current_user.get("tenant_id", "tenant-default")
    user_id = current_user.get("sub", "user-default")
    roles = current_user.get("roles", [])
    
    order = check_bola_order(order_id, tenant_id, user_id, roles)
    return OrderResponse(**order.to_dict())

@app.put("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    order: OrderCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    tenant_id = current_user.get("tenant_id", "tenant-default")
    user_id = current_user.get("sub", "user-default")
    roles = current_user.get("roles", [])
    
    check_bola_order(order_id, tenant_id, user_id, roles)
    
    repo = OrderRepository(db_manager, tenant_id)
    update_data = {
        "product_id": order.product_id,
        "quantity": order.quantity,
        "total_amount": order.total_amount
    }
    updated = repo.update_order(order_id, update_data)
    return OrderResponse(**updated.to_dict())

@app.delete("/api/v1/orders/{order_id}")
async def delete_order(
    order_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    tenant_id = current_user.get("tenant_id", "tenant-default")
    user_id = current_user.get("sub", "user-default")
    roles = current_user.get("roles", [])
    
    check_bola_order(order_id, tenant_id, user_id, roles)
    
    repo = OrderRepository(db_manager, tenant_id)
    deleted = repo.delete_order(order_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted successfully"}

# ============ INCLUDE ROUTERS ============
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

# ============ ERROR HANDLERS ============
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "path": request.url.path}
    )

# ============ RUNTIME PROVENANCE ============
from sentinelayer.security.provenance import get_provenance
provenance = get_provenance()
logger.info(f"🔐 Runtime provenance status: {provenance.get_status()}")

# Kalo di production dan gagal, exit
if ENVIRONMENT == "production" and not provenance.verified:
    logger.critical("❌ Runtime provenance verification failed in production!")
    raise RuntimeError("Runtime provenance verification failed")
