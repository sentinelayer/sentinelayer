from sqlalchemy import Column, String, Boolean, DateTime
import uuid
from datetime import datetime
from src.sentinelayer.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    tenant_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
