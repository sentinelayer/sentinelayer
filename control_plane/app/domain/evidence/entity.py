"""
Evidence — First-Class Object (Blueprint Section 0.5)

Required fields:
Evidence ID, Requirement ID, Control ID, Artifact, Timestamp,
Hash (SHA-256), Owner, Reviewer, Retention, Validity,
Chain of Custody, Relationship, Implementation Version,
Runtime Provenance (2026).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String, Text

from control_plane.app.infrastructure.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String(64), nullable=False, index=True)
    control_id = Column(String(64), nullable=False, index=True)
    artifact = Column(Text, nullable=False)
    artifact_type = Column(String(32), default="file")

    hash_sha256 = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=True)

    owner = Column(String(128), nullable=False)
    reviewer = Column(String(128), nullable=True)

    status = Column(String(16), default="CREATED", index=True)

    implementation_version = Column(String(64), nullable=False)
    current_system_version = Column(String(64), nullable=True)

    runtime_artifact_hash = Column(String(64), nullable=True)
    approved_manifest_hash = Column(String(64), nullable=True)

    retention_days = Column(String(16), default="2555")
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)

    relationship = Column(String(64), nullable=True)
    related_id = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=_utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    validated_at = Column(DateTime, nullable=True)
    expired_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(Text, nullable=True)

    chain_of_custody = Column(Text, default="[]")
