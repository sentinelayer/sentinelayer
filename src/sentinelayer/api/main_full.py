from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import uuid
from pydantic import BaseModel
from typing import List, Optional

from sentinelayer.api.routes import auth
from sentinelayer.database.models.base import DatabaseManager
from sentinelayer.database.models.order import OrderRepository, OrderStatus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Init database
db_manager = DatabaseManager()
db_manager.create_tables()

# Create FastAPI app
app = FastAPI(
    title="SentinelLayer API",
    description="Security control and enforcement platform",
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
        "database": "postgresql"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/metrics")
async def metrics():
    return {"message": "Metrics endpoint"}

# ============ ORDERS ============

@app.post("/api/v1/orders/", response_model=OrderResponse)
async def create_order(order: OrderCreate, request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "tenant-default")
    user_id = request.headers.get("X-User-ID", "user-default")
    
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
async def list_orders(request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "tenant-default")
    
    repo = OrderRepository(db_manager, tenant_id)
    orders = repo.get_all_orders()
    
    return [OrderResponse(**order.to_dict()) for order in orders]

@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "tenant-default")
    
    repo = OrderRepository(db_manager, tenant_id)
    order = repo.get_order(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return OrderResponse(**order.to_dict())

@app.put("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def update_order(order_id: str, order: OrderCreate, request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "tenant-default")
    
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
async def delete_order(order_id: str, request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "tenant-default")
    
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

# ============ METRICS MIDDLEWARE ============
from sentinelayer.observability.metrics import (
    record_request, increment_active_requests, decrement_active_requests
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    increment_active_requests()
    start_time = time.time()
    
    try:
        response = await call_next(request)
    except Exception as e:
        duration = time.time() - start_time
        record_request(
            method=request.method,
            endpoint=request.url.path,
            tenant=getattr(request.state, 'tenant_id', 'unknown'),
            status_code=500,
            duration=duration
        )
        decrement_active_requests()
        raise e
    
    duration = time.time() - start_time
    record_request(
        method=request.method,
        endpoint=request.url.path,
        tenant=getattr(request.state, 'tenant_id', 'unknown'),
        status_code=response.status_code,
        duration=duration
    )
    decrement_active_requests()
    return response

# ============ THREAT INTELLIGENCE + AI ============
from sentinelayer.threatintel.engine import get_threat_intel
from sentinelayer.ai.llm import get_llm_layer

threat_intel = get_threat_intel()
llm_layer = get_llm_layer()

@app.get("/api/v1/threatintel/check")
async def check_threatintel(ip: str):
    result = threat_intel.check_ip(ip)
    return {
        "ip": result.ip,
        "score": result.score,
        "is_malicious": result.is_malicious,
        "categories": result.categories,
        "source": result.source
    }

@app.get("/api/v1/ai/analyze")
async def analyze_request(request: Request):
    request_data = {
        "request_id": request.headers.get("X-Request-ID", "unknown"),
        "method": request.method,
        "endpoint": request.url.path,
        "user_id": getattr(request.state, "user_id", "unknown"),
        "tenant_id": getattr(request.state, "tenant_id", "unknown"),
        "client_ip": request.client.host if request.client else "unknown",
        "url": str(request.url)
    }
    
    # Mock risk result
    risk_result = {
        "score": 0.3,
        "level": "low",
        "decision": "allow",
        "confidence": 0.8,
        "signals": []
    }
    
    analysis = llm_layer.analyze_request(request_data, risk_result)
    return {
        "request_id": analysis.request_id,
        "summary": analysis.summary,
        "risk_level": analysis.risk_level,
        "recommendations": analysis.recommendations,
        "confidence": analysis.confidence
    }
