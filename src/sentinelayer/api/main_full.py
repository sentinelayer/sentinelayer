from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import time
import logging
import uuid
import os
from pydantic import BaseModel
from typing import List, Optional

from sentinelayer.api.routes import auth
from sentinelayer.database.models.base import DatabaseManager
from sentinelayer.database.models.order import OrderRepository, OrderStatus
from sentinelayer.backend.internal.auth.authorization import AuthorizationMiddleware, Resource

from sentinelayer.api.middleware.auth import AuthMiddleware
from sentinelayer.api.middleware.waf import WAFMiddleware
from sentinelayer.api.middleware.ratelimit import RateLimitMiddleware
from sentinelayer.api.middleware.tenant import TenantMiddleware
from sentinelayer.api.middleware.pipeline import security_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
TESTING = os.getenv("TESTING", "false").lower() == "true"

if TESTING and ENVIRONMENT == "production":
    raise RuntimeError("TESTING mode is NOT allowed in production environment!")

db_manager = DatabaseManager()
db_manager.create_tables()

app = FastAPI(
    title="SentinelLayer API",
    description="Security control and enforcement platform",
    version="0.1.0",
    docs_url="/docs"
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    max_age=86400,
)

auth_middleware = AuthMiddleware()
waf_middleware = WAFMiddleware()
rate_limit_middleware = RateLimitMiddleware()
tenant_middleware = TenantMiddleware()
bola_middleware = AuthorizationMiddleware()

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
        await auth_middleware(request)
        await rate_limit_middleware(request)
        await tenant_middleware(request)
    
    return await security_pipeline(request, call_next)

async def get_current_user(request: Request):
    if TESTING:
        return {"sub": "test-user", "tenant_id": "tenant-test", "roles": ["user"]}
    user = getattr(request.state, 'user', None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

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
    from fastapi.responses import Response
    from sentinelayer.observability.metrics import get_metrics
    return Response(content=get_metrics(), media_type="text/plain")

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

@app.post("/api/v1/orders/", response_model=OrderResponse)
async def create_order(order: OrderCreate, request: Request, current_user: dict = Depends(get_current_user)):
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
async def list_orders(request: Request, current_user: dict = Depends(get_current_user)):
    tenant_id = current_user.get("tenant_id", "tenant-default")
    repo = OrderRepository(db_manager, tenant_id)
    orders = repo.get_all_orders()
    return [OrderResponse(**order.to_dict()) for order in orders]

@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    tenant_id = current_user.get("tenant_id", "tenant-default")
    user_id = current_user.get("sub", "user-default")
    roles = current_user.get("roles", [])
    order = check_bola_order(order_id, tenant_id, user_id, roles)
    return OrderResponse(**order.to_dict())

@app.put("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def update_order(order_id: str, order: OrderCreate, request: Request, current_user: dict = Depends(get_current_user)):
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
async def delete_order(order_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    tenant_id = current_user.get("tenant_id", "tenant-default")
    user_id = current_user.get("sub", "user-default")
    roles = current_user.get("roles", [])
    check_bola_order(order_id, tenant_id, user_id, roles)
    repo = OrderRepository(db_manager, tenant_id)
    deleted = repo.delete_order(order_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted successfully"}

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

from sentinelayer.risk.engine import get_risk_engine
from sentinelayer.behavior.baseline import get_baseline_manager
from sentinelayer.decision.safety import get_decision_safety
from sentinelayer.threatintel.engine import get_threat_intel
from sentinelayer.ai.llm import get_llm_layer
from sentinelayer.evidence.gate import get_gate_engine
from sentinelayer.evidence.matrix import get_evidence_matrix
from sentinelayer.security.key_rotation import get_key_rotation
from sentinelayer.controlplane.models import get_control_plane

risk_engine = get_risk_engine()
behavior_engine = get_baseline_manager()
decision_safety = get_decision_safety()
threat_intel = get_threat_intel()
llm_layer = get_llm_layer()
gate_engine = get_gate_engine()
evidence_matrix = get_evidence_matrix()
key_rotation = get_key_rotation()
control_plane = get_control_plane()

@app.get("/api/v1/risk/calculate")
async def risk_calculate(current_user: dict = Depends(get_current_user)):
    signals = []
    return risk_engine.calculate_risk(signals)

@app.post("/api/v1/risk/signal")
async def risk_signal(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    return {"status": "signal_received"}

@app.get("/api/v1/behavior/stats")
async def behavior_stats(current_user: dict = Depends(get_current_user)):
    return behavior_engine.get_stats()

@app.get("/api/v1/decision/stats")
async def decision_stats(current_user: dict = Depends(get_current_user)):
    return decision_safety.get_stats()

@app.post("/api/v1/decision/killswitch")
async def toggle_killswitch(request: Request, current_user: dict = Depends(get_current_user)):
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin role required")
    data = await request.json()
    if data.get("action") == "activate":
        decision_safety.activate_kill_switch(data.get("reason", "Manual"))
        return {"status": "activated"}
    decision_safety.deactivate_kill_switch()
    return {"status": "deactivated"}

@app.get("/api/v1/threatintel/ip/{ip}")
async def threat_ip(ip: str, current_user: dict = Depends(get_current_user)):
    result = threat_intel.check_ip(ip)
    return {"ip": ip, "score": result.score, "is_malicious": result.is_malicious}

@app.post("/api/v1/ai/analyze")
async def ai_analyze(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    analysis = llm_layer.analyze_request(data.get("request", {}), data.get("risk", {}))
    return {"summary": analysis.summary, "recommendations": analysis.recommendations}

@app.get("/api/v1/gate/check/{requirement_id}")
async def gate_check(requirement_id: str, current_user: dict = Depends(get_current_user)):
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin role required")
    result = gate_engine.check_requirement(requirement_id, requirement_id)
    return gate_engine.get_status(requirement_id)

@app.get("/api/v1/evidence/list")
async def evidence_list(current_user: dict = Depends(get_current_user)):
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin role required")
    return {"evidence": [e.__dict__ for e in evidence_matrix.list_evidence()]}

@app.get("/api/v1/keys/status")
async def keys_status(current_user: dict = Depends(get_current_user)):
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin role required")
    return key_rotation.get_stats()

@app.post("/api/v1/keys/rotate")
async def keys_rotate(current_user: dict = Depends(get_current_user)):
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin role required")
    key_rotation.rotate_key(key_rotation.current_key_id, current_user.get("sub", "system"))
    return {"status": "rotated", "new_key": key_rotation.current_key_id}

@app.post("/api/v1/tenants")
async def create_tenant(data: dict, current_user: dict = Depends(get_current_user)):
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin required")
    tenant = control_plane.create_tenant(data.get("name"), data.get("description", ""))
    return {"id": tenant.id, "name": tenant.name}

@app.get("/api/v1/tenants")
async def list_tenants(current_user: dict = Depends(get_current_user)):
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin required")
    return [{"id": t.id, "name": t.name} for t in control_plane.list_tenants()]

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "path": request.url.path}
    )
from sentinelayer.security.provenance import get_provenance
provenance = get_provenance()
logger.info(f"Runtime provenance status: {provenance.get_status()}")
from sentinelayer.api.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
from sentinelayer.security.attestation import get_attestation
attestation = get_attestation()
logger.info(f"Runtime attestation: {attestation.get_status()}")
