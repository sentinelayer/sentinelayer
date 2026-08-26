import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String

from control_plane.app.infrastructure.db.session import Base


class Application(Base):
    __tablename__ = "applications"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
