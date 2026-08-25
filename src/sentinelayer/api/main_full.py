from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import uuid
import os
from pydantic import BaseModel
from typing import List, Optional

from sentinelayer.api.routes import auth
from sentinelayer.database.models.base import DatabaseManager
from sentinelayer.database.models.order import OrderRepository, OrderStatus

# ============ MIDDLEWARE ============
from sentinelayer.api.middleware.auth import AuthMiddleware
from sentinelayer.api.middleware.waf import WAFMiddleware
from sentinelayer.api.middleware.ratelimit import RateLimitMiddleware
from sentinelayer.api.middleware.tenant import TenantMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_manager = DatabaseManager()
db_manager.create_tables()

app = FastAPI(
    title="SentinelLayer API",
    description="Security control and enforcement platform",
    version="0.1.0",
    docs_url="/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ TESTING MODE ============
TESTING = os.getenv("TESTING", "false").lower() == "true"
if TESTING:
    logger.warning("⚠️ RUNNING IN TESTING MODE - AUTH DISABLED")

# ============ INIT MIDDLEWARE ============
auth_middleware = AuthMiddleware()
waf_middleware = WAFMiddleware()
rate_limit_middleware = RateLimitMiddleware()
tenant_middleware = TenantMiddleware()

# ============ GLOBAL SECURITY MIDDLEWARE ============
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    public_paths = ["/", "/health", "/docs", "/redoc", "/openapi.json", "/metrics", "/api/v1/auth/login"]
    
    # Kalo testing, skip auth
    if TESTING:
        # Tetap jalanin WAF & rate limit kalo mau
        if request.url.path not in public_paths:
            await waf_middleware(request)
            await rate_limit_middleware(request)
            # SKIP AUTH
        response = await call_next(request)
        return response
    
    # Production: jalanin semua middleware
    if request.url.path not in public_paths:
        await waf_middleware(request)
        await rate_limit_middleware(request)
        await auth_middleware(request)  # <- AUTH ONLY IN PRODUCTION
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
        "security": {
            "waf": "enabled",
            "rate_limit": "enabled",
            "auth": "disabled (testing)" if TESTING else "enabled",
            "tenant_isolation": "enabled"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/metrics")
async def metrics():
    return {"message": "Metrics endpoint"}

# ============ ORDERS ============
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
    
    repo = OrderRepository(db_manager, tenant_id)
    order = repo.get_order(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return OrderResponse(**order.to_dict())

@app.put("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def update_order(order_id: str, order: OrderCreate, request: Request, current_user: dict = Depends(get_current_user)):
    tenant_id = current_user.get("tenant_id", "tenant-default")
    
    repo = OrderRepository(db_manager, tenant_id)
    
    update_data = {
        "product_id": order.product_id,
        "quantity": order.quantity,
        "total_amount": order.total_amount
    }
    
    updated = repo.update_order(order_id, update_data)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return OrderResponse(**updated.to_dict())

@app.delete("/api/v1/orders/{order_id}")
async def delete_order(order_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    tenant_id = current_user.get("tenant_id", "tenant-default")
    
    repo = OrderRepository(db_manager, tenant_id)
    deleted = repo.delete_order(order_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order deleted successfully"}

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "path": request.url.path}
    )

# Security Headers
from sentinelayer.api.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# ============ ENGINE INTEGRATION ============
from sentinelayer.behavior.baseline import get_baseline_manager
from sentinelayer.risk.engine import get_risk_engine
from sentinelayer.decision.safety import get_decision_safety
from sentinelayer.controlplane.models import get_control_plane
from sentinelayer.threatintel.engine import get_threat_intel
from sentinelayer.ai.llm import get_llm_layer
from sentinelayer.evidence.matrix import get_evidence_matrix
from sentinelayer.evidence.gate import get_gate_engine
from sentinelayer.security.key_rotation import get_key_rotation

# Init engines
behavior_engine = get_baseline_manager()
risk_engine = get_risk_engine()
decision_safety = get_decision_safety()
control_plane = get_control_plane()
threat_intel = get_threat_intel()
llm_layer = get_llm_layer()
evidence_matrix = get_evidence_matrix()
gate_engine = get_gate_engine()
key_rotation = get_key_rotation()

# ============ BEHAVIOR ENGINE ENDPOINTS ============
@app.post("/api/v1/behavior/record")
async def record_behavior(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    result = behavior_engine.record_request({
        "endpoint": data.get("endpoint", request.url.path),
        "method": request.method,
        "user_id": current_user.get("sub", "unknown"),
        "tenant_id": current_user.get("tenant_id", "default"),
        "response_time": data.get("response_time", 0),
        "status_code": data.get("status_code", 200),
        "request_size": data.get("request_size", 0),
        "response_size": data.get("response_size", 0)
    })
    return {"status": "recorded", "profile": result.__dict__ if hasattr(result, "__dict__") else str(result)}

@app.get("/api/v1/behavior/detect")
async def detect_anomaly(request: Request, current_user: dict = Depends(get_current_user)):
    result = behavior_engine.detect_anomaly({
        "endpoint": request.url.path,
        "method": request.method,
        "user_id": current_user.get("sub", "unknown"),
        "tenant_id": current_user.get("tenant_id", "default"),
        "response_time": float(request.headers.get("X-Response-Time", 0)),
        "status_code": 200
    })
    return result

@app.get("/api/v1/behavior/stats")
async def behavior_stats(current_user: dict = Depends(get_current_user)):
    return behavior_engine.get_stats()

# ============ RISK ENGINE ENDPOINTS ============
@app.post("/api/v1/risk/signal")
async def add_risk_signal(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    risk_engine.add_signal(
        name=data.get("name", "unknown"),
        score=data.get("score", 0.5),
        source=data.get("source", "api"),
        details=data.get("details", {})
    )
    return {"status": "signal_added"}

@app.get("/api/v1/risk/calculate")
async def calculate_risk(current_user: dict = Depends(get_current_user)):
    result = risk_engine.calculate_risk()
    return result

@app.post("/api/v1/risk/clear")
async def clear_risk_signals(current_user: dict = Depends(get_current_user)):
    risk_engine.clear_signals()
    return {"status": "cleared"}

# ============ DECISION SAFETY ENDPOINTS ============
@app.post("/api/v1/decision/make")
async def make_decision(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    risk_result = data.get("risk_result", {"score": 0.5, "level": "low", "decision": "allow", "confidence": 0.8, "signals": []})
    decision = decision_safety.make_decision(
        request_id=request.headers.get("X-Request-ID", "unknown"),
        risk_result=risk_result,
        context={"user": current_user.get("sub"), "path": request.url.path}
    )
    return {
        "action": decision.action,
        "risk_level": decision.risk_level,
        "risk_score": decision.risk_score,
        "confidence": decision.confidence,
        "reason": decision.reason
    }

@app.post("/api/v1/decision/killswitch")
async def toggle_killswitch(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    action = data.get("action", "activate")
    if action == "activate":
        decision_safety.activate_kill_switch(data.get("reason", "Manual trigger"))
        return {"status": "killswitch_activated"}
    else:
        decision_safety.deactivate_kill_switch()
        return {"status": "killswitch_deactivated"}

@app.get("/api/v1/decision/stats")
async def decision_stats(current_user: dict = Depends(get_current_user)):
    return decision_safety.get_stats()

# ============ CONTROL PLANE ENDPOINTS ============
@app.post("/api/v1/control/tenant")
async def create_tenant(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    tenant = control_plane.create_tenant(
        name=data.get("name", "default"),
        description=data.get("description", ""),
        settings=data.get("settings", {})
    )
    return {"id": tenant.id, "name": tenant.name, "created_at": tenant.created_at}

@app.get("/api/v1/control/tenants")
async def list_tenants(current_user: dict = Depends(get_current_user)):
    return [{"id": t.id, "name": t.name, "is_active": t.is_active} for t in control_plane.list_tenants()]

@app.post("/api/v1/control/application")
async def create_application(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    app = control_plane.create_application(
        tenant_id=data.get("tenant_id", "default"),
        name=data.get("name", "default"),
        description=data.get("description", ""),
        endpoints=data.get("endpoints", [])
    )
    return {"id": app.id, "name": app.name, "tenant_id": app.tenant_id}

@app.post("/api/v1/control/policy")
async def create_policy(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    policy = control_plane.create_policy(
        tenant_id=data.get("tenant_id", "default"),
        name=data.get("name", "default"),
        policy_type=data.get("type", "waf"),
        rules=data.get("rules", [])
    )
    return {"id": policy.id, "name": policy.name, "type": policy.type}

@app.get("/api/v1/control/stats")
async def control_stats(current_user: dict = Depends(get_current_user)):
    return control_plane.get_stats()

# ============ THREAT INTELLIGENCE ENDPOINTS ============
@app.get("/api/v1/threatintel/ip/{ip}")
async def check_ip(ip: str, current_user: dict = Depends(get_current_user)):
    result = threat_intel.check_ip(ip)
    return {
        "ip": result.ip,
        "score": result.score,
        "is_malicious": result.is_malicious,
        "categories": result.categories,
        "source": result.source
    }

@app.get("/api/v1/threatintel/domain/{domain}")
async def check_domain(domain: str, current_user: dict = Depends(get_current_user)):
    result = threat_intel.check_domain(domain)
    return {
        "domain": domain,
        "score": result.score,
        "is_malicious": result.is_malicious,
        "categories": result.categories,
        "source": result.source
    }

# ============ AI/LLM ENDPOINTS ============
@app.post("/api/v1/ai/analyze")
async def ai_analyze(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    risk_result = data.get("risk_result", {"score": 0.3, "level": "low", "decision": "allow", "confidence": 0.8, "signals": []})
    analysis = llm_layer.analyze_request(
        request_data={
            "request_id": request.headers.get("X-Request-ID", "unknown"),
            "method": request.method,
            "endpoint": request.url.path,
            "user_id": current_user.get("sub", "unknown"),
            "tenant_id": current_user.get("tenant_id", "default"),
            "client_ip": request.client.host if request.client else "unknown"
        },
        risk_result=risk_result
    )
    return {
        "request_id": analysis.request_id,
        "summary": analysis.summary,
        "risk_level": analysis.risk_level,
        "recommendations": analysis.recommendations,
        "confidence": analysis.confidence
    }

# ============ EVIDENCE MATRIX ENDPOINTS ============
@app.post("/api/v1/evidence/create")
async def create_evidence(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    evidence = evidence_matrix.create_evidence(
        requirement_id=data.get("requirement_id", "REQ-001"),
        control_id=data.get("control_id", "CTRL-001"),
        artifact=data.get("artifact", "test_artifact")
    )
    return {"evidence_id": evidence.evidence_id, "status": evidence.status}

@app.get("/api/v1/evidence/list")
async def list_evidence(current_user: dict = Depends(get_current_user)):
    return {
        "evidence": [{"id": e.evidence_id, "status": e.status, "requirement": e.requirement_id} for e in evidence_matrix.list_evidence()],
        "stats": evidence_matrix.get_stats()
    }

@app.post("/api/v1/evidence/verify/{evidence_id}")
async def verify_evidence(evidence_id: str, current_user: dict = Depends(get_current_user)):
    result = evidence_matrix.verify_evidence(evidence_id, current_user.get("sub", "system"))
    return {"status": "verified" if result else "failed"}

# ============ GATE ENGINE ENDPOINTS ============
@app.get("/api/v1/gate/check/{requirement_id}")
async def check_gate(requirement_id: str, current_user: dict = Depends(get_current_user)):
    result = gate_engine.check_requirement(requirement_id, "EV-001")
    return gate_engine.get_status(requirement_id)

# ============ KEY ROTATION ENDPOINTS ============
@app.get("/api/v1/keys/status")
async def key_status(current_user: dict = Depends(get_current_user)):
    return key_rotation.get_stats()

@app.post("/api/v1/keys/rotate")
async def rotate_keys(current_user: dict = Depends(get_current_user)):
    key_rotation.rotate_key(key_rotation.current_key_id, current_user.get("sub", "system"))
    return {"message": "Keys rotated", "new_key_id": key_rotation.current_key_id}

# ============ RUNTIME PROVENANCE ============
from sentinelayer.security.provenance import get_provenance
provenance = get_provenance()

@app.get("/api/v1/provenance/verify/{artifact_id}")
async def verify_provenance(artifact_id: str, current_user: dict = Depends(get_current_user)):
    result = provenance.verify_artifact(f"src/sentinelayer/api/main_full.py", artifact_id)
    return {"artifact_id": artifact_id, "verified": result}

@app.post("/api/v1/provenance/record")
async def record_provenance(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    provenance.record_artifact(
        artifact_id=data.get("artifact_id", "main_app"),
        artifact_path=data.get("artifact_path", "src/sentinelayer/api/main_full.py"),
        version=data.get("version", "0.1.0")
    )
    return {"status": "recorded"}
