from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import uuid
from pydantic import BaseModel, EmailStr
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

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

# ============ STORAGE ============

orders_db = {}

# ============ ROOT ============

@app.get("/")
async def root():
    return {
        "service": "SentinelLayer",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/metrics")
async def metrics():
    return {"message": "Metrics endpoint"}

# ============ AUTH ============

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    if not request.email or not request.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password required"
        )
    
    # Simple token (tanpa JWT library untuk sementara)
    token = f"fake-token-{uuid.uuid4()}-{int(time.time())}"
    
    return LoginResponse(
        access_token=token,
        expires_in=900
    )

# ============ ORDERS ============

@app.post("/api/v1/orders/", response_model=OrderResponse)
async def create_order(order: OrderCreate, request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "tenant-default")
    user_id = request.headers.get("X-User-ID", "user-default")
    
    order_id = str(uuid.uuid4())
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    order_data = {
        "id": order_id,
        "user_id": user_id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "total_amount": order.total_amount,
        "status": "pending",
        "tenant_id": tenant_id,
        "created_at": now,
        "updated_at": now
    }
    
    orders_db[order_id] = order_data
    return OrderResponse(**order_data)

@app.get("/api/v1/orders/", response_model=List[OrderResponse])
async def list_orders(request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "tenant-default")
    
    result = [
        OrderResponse(**order) 
        for order in orders_db.values() 
        if order["tenant_id"] == tenant_id
    ]
    return result

@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "tenant-default")
    
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return OrderResponse(**order)

@app.put("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def update_order(order_id: str, order: OrderCreate, request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "tenant-default")
    
    existing = orders_db.get(order_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if existing["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    existing["product_id"] = order.product_id
    existing["quantity"] = order.quantity
    existing["total_amount"] = order.total_amount
    existing["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    return OrderResponse(**existing)

@app.delete("/api/v1/orders/{order_id}")
async def delete_order(order_id: str, request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "tenant-default")
    
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    del orders_db[order_id]
    return {"message": "Order deleted"}

# ============ ERROR HANDLERS ============

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "path": request.url.path}
    )
