from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Optional
import uuid

from sentinelayer.api.middleware.auth import get_current_user, get_current_tenant
from sentinelayer.backend.internal.auth.jwt_handler import TokenPayload
from sentinelayer.database.models.order import OrderRepository
from sentinelayer.database.models.base import DatabaseManager

router = APIRouter()
db_manager = DatabaseManager()

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

@router.post("/", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    current_tenant: str = Depends(get_current_tenant)
):
    """Create new order (with tenant isolation)"""
    
    repo = OrderRepository(db_manager, current_tenant)
    
    order_data = {
        "user_id": current_user.sub,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "total_amount": order.total_amount,
        "created_by": current_user.sub
    }
    
    try:
        created_order = repo.create_order(order_data)
        return OrderResponse(
            id=created_order.id,
            user_id=created_order.user_id,
            product_id=created_order.product_id,
            quantity=created_order.quantity,
            total_amount=created_order.total_amount,
            status=created_order.status,
            tenant_id=created_order.tenant_id,
            created_at=created_order.created_at.isoformat(),
            updated_at=created_order.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    current_tenant: str = Depends(get_current_tenant)
):
    """Get order by ID (with tenant isolation)"""
    
    repo = OrderRepository(db_manager, current_tenant)
    order = repo.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        product_id=order.product_id,
        quantity=order.quantity,
        total_amount=order.total_amount,
        status=order.status,
        tenant_id=order.tenant_id,
        created_at=order.created_at.isoformat(),
        updated_at=order.updated_at.isoformat()
    )

@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    user_id: Optional[str] = None,
    current_user: TokenPayload = Depends(get_current_user),
    current_tenant: str = Depends(get_current_tenant)
):
    """List orders (with tenant isolation)"""
    
    repo = OrderRepository(db_manager, current_tenant)
    
    # Use current user if no user_id provided
    target_user = user_id or current_user.sub
    
    orders = repo.get_user_orders(target_user)
    
    return [
        OrderResponse(
            id=order.id,
            user_id=order.user_id,
            product_id=order.product_id,
            quantity=order.quantity,
            total_amount=order.total_amount,
            status=order.status,
            tenant_id=order.tenant_id,
            created_at=order.created_at.isoformat(),
            updated_at=order.updated_at.isoformat()
        )
        for order in orders
    ]

@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    updates: OrderCreate,
    current_user: TokenPayload = Depends(get_current_user),
    current_tenant: str = Depends(get_current_tenant)
):
    """Update order (with tenant isolation)"""
    
    repo = OrderRepository(db_manager, current_tenant)
    
    update_data = {
        "product_id": updates.product_id,
        "quantity": updates.quantity,
        "total_amount": updates.total_amount
    }
    
    order = repo.update_order(order_id, update_data)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        product_id=order.product_id,
        quantity=order.quantity,
        total_amount=order.total_amount,
        status=order.status,
        tenant_id=order.tenant_id,
        created_at=order.created_at.isoformat(),
        updated_at=order.updated_at.isoformat()
    )

@router.delete("/{order_id}")
async def delete_order(
    order_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    current_tenant: str = Depends(get_current_tenant)
):
    """Delete order (with tenant isolation)"""
    
    repo = OrderRepository(db_manager, current_tenant)
    deleted = repo.delete_order(order_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return {"message": "Order deleted successfully"}
