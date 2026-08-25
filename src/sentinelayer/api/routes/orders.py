from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

router = APIRouter()

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

# In-memory storage (sementara)
orders_db = {}

@router.post("/", response_model=OrderResponse)
async def create_order(order: OrderCreate, request: Request):
    """Create new order"""
    tenant_id = getattr(request.state, "tenant_id", "tenant-default")
    user_id = getattr(request.state, "user_id", "user-default")
    
    order_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
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

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, request: Request):
    """Get order by ID"""
    tenant_id = getattr(request.state, "tenant_id", "tenant-default")
    
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return OrderResponse(**order)

@router.get("/", response_model=List[OrderResponse])
async def list_orders(request: Request):
    """List all orders"""
    tenant_id = getattr(request.state, "tenant_id", "tenant-default")
    
    tenant_orders = [
        order for order in orders_db.values()
        if order["tenant_id"] == tenant_id
    ]
    
    return [OrderResponse(**order) for order in tenant_orders]

@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(order_id: str, updates: OrderCreate, request: Request):
    """Update order"""
    tenant_id = getattr(request.state, "tenant_id", "tenant-default")
    
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    order["product_id"] = updates.product_id
    order["quantity"] = updates.quantity
    order["total_amount"] = updates.total_amount
    order["updated_at"] = datetime.now().isoformat()
    
    return OrderResponse(**order)

@router.delete("/{order_id}")
async def delete_order(order_id: str, request: Request):
    """Delete order"""
    tenant_id = getattr(request.state, "tenant_id", "tenant-default")
    
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    del orders_db[order_id]
    return {"message": "Order deleted successfully"}
