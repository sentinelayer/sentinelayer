from sqlalchemy import Column, String, DateTime
from control_plane.app.infrastructure.db.session import Base
from datetime import datetime
import uuid

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
