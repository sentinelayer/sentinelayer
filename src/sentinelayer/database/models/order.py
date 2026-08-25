from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .base import Base, TenantAwareMixin
import enum
import uuid
from datetime import datetime

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

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
    def __init__(self, db_manager, tenant_id: str):
        self.db_manager = db_manager
        self.tenant_id = tenant_id
    
    def _apply_tenant_filter(self, query):
        return query.filter(Order.tenant_id == self.tenant_id)
    
    def create_order(self, order_data: dict) -> Order:
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
        
        with self.db_manager.get_session(self.tenant_id) as session:
            session.add(order)
            session.commit()
            session.refresh(order)
            return order
    
    def get_order(self, order_id: str) -> Order | None:
        with self.db_manager.get_session(self.tenant_id) as session:
            query = session.query(Order).filter(Order.id == order_id)
            if self.db_manager.is_sqlite:
                query = self._apply_tenant_filter(query)
            return query.first()
    
    def get_user_orders(self, user_id: str) -> list[Order]:
        with self.db_manager.get_session(self.tenant_id) as session:
            query = session.query(Order).filter(Order.user_id == user_id)
            if self.db_manager.is_sqlite:
                query = self._apply_tenant_filter(query)
            return query.all()
    
    def get_all_orders(self) -> list[Order]:
        with self.db_manager.get_session(self.tenant_id) as session:
            query = session.query(Order)
            if self.db_manager.is_sqlite:
                query = self._apply_tenant_filter(query)
            return query.all()
    
    def update_order(self, order_id: str, updates: dict) -> Order | None:
        with self.db_manager.get_session(self.tenant_id) as session:
            query = session.query(Order).filter(Order.id == order_id)
            if self.db_manager.is_sqlite:
                query = self._apply_tenant_filter(query)
            order = query.first()
            if not order:
                return None
            
            for key, value in updates.items():
                if hasattr(order, key):
                    setattr(order, key, value)
            
            session.commit()
            session.refresh(order)
            return order
    
    def delete_order(self, order_id: str) -> bool:
        with self.db_manager.get_session(self.tenant_id) as session:
            query = session.query(Order).filter(Order.id == order_id)
            if self.db_manager.is_sqlite:
                query = self._apply_tenant_filter(query)
            order = query.first()
            if not order:
                return False
            
            session.delete(order)
            session.commit()
            return True
