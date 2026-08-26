from sqlalchemy import Column, String, DateTime
from control_plane.app/infrastructure/db/session import Base
from datetime import datetime
import uuid

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    artifact = Column(String, nullable=False)
    requirement_id = Column(String, nullable=False)
    control_id = Column(String, nullable=False)
    status = Column(String, default="CREATED")
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
