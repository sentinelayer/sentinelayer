from sqlalchemy import Column, String, Integer, Float
from .base import Base, TenantAwareMixin
import uuid
import time

class OrderStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Order(Base, TenantAwareMixin):
    __tablename__ = "orders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    product_id = Column(String(36), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(20), default=OrderStatus.PENDING)
    created_by = Column(String(36), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "total_amount": self.total_amount,
            "status": self.status,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class OrderRepository:
    """Repository untuk operasi Order dengan tenant isolation"""
    
    def __init__(self, db_manager, tenant_id: str):
        self.db_manager = db_manager
        self.tenant_id = tenant_id
    
    def create_order(self, order_data: dict) -> Order:
        """Create new order with tenant isolation"""
        order = Order(
            id=order_data.get("id", str(uuid.uuid4())),
            user_id=order_data["user_id"],
            product_id=order_data["product_id"],
            quantity=order_data["quantity"],
            total_amount=order_data["total_amount"],
            tenant_id=self.tenant_id,
            created_by=order_data.get("created_by", "system"),
            status=order_data.get("status", OrderStatus.PENDING)
        )
        
        with self.db_manager.get_session() as session:
            session.add(order)
            session.commit()
            session.refresh(order)
            return order
    
    def get_order(self, order_id: str):
        """Get order by ID with tenant isolation"""
        with self.db_manager.get_session() as session:
            return session.query(Order).filter(
                Order.id == order_id,
                Order.tenant_id == self.tenant_id
            ).first()
    
    def get_all_orders(self):
        """Get all orders for this tenant"""
        with self.db_manager.get_session() as session:
            return session.query(Order).filter(
                Order.tenant_id == self.tenant_id
            ).all()
    
    def get_user_orders(self, user_id: str):
        """Get orders for specific user within tenant"""
        with self.db_manager.get_session() as session:
            return session.query(Order).filter(
                Order.tenant_id == self.tenant_id,
                Order.user_id == user_id
            ).all()
    
    def update_order(self, order_id: str, updates: dict):
        """Update order with tenant isolation"""
        with self.db_manager.get_session() as session:
            order = session.query(Order).filter(
                Order.id == order_id,
                Order.tenant_id == self.tenant_id
            ).first()
            if not order:
                return None
            
            for key, value in updates.items():
                if hasattr(order, key):
                    setattr(order, key, value)
            
            session.commit()
            session.refresh(order)
            return order
    
    def delete_order(self, order_id: str) -> bool:
        """Delete order with tenant isolation"""
        with self.db_manager.get_session() as session:
            order = session.query(Order).filter(
                Order.id == order_id,
                Order.tenant_id == self.tenant_id
            ).first()
            if not order:
                return False
            
            session.delete(order)
            session.commit()
            return True
