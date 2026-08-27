import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String

from control_plane.app.infrastructure.db.session import Base


class BreakGlass(Base):
    __tablename__ = "breakglass"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, default="PENDING")
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
