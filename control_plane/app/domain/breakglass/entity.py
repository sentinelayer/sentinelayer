from sqlalchemy import Column, String, DateTime
from control_plane/app/infrastructure/db/session import Base
from datetime import datetime
import uuid

class BreakGlass(Base):
    __tablename__ = "breakglass"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, default="PENDING")
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
