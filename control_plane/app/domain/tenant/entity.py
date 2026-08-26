import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String

from control_plane.app.infrastructure.db.session import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
