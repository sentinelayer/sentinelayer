import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from control_plane.app.infrastructure.db.session import Base


def _utcnow():
    return datetime.now(UTC)


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=_utcnow)


class Application(Base):
    __tablename__ = "applications"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), index=True)
    environment = Column(String, default="production")
    created_at = Column(DateTime, default=_utcnow)


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), index=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)
    mfa_backup_codes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class Policy(Base):
    __tablename__ = "policies"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    rules = Column(String, nullable=False)
    application_id = Column(String, ForeignKey("applications.id"), nullable=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), index=True, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    severity = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, default="open")
    tenant_id = Column(String, ForeignKey("tenants.id"), index=True)
    created_at = Column(DateTime, default=_utcnow)


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


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(String(64), primary_key=True)
    owner = Column(String(128), nullable=False)
    dependency = Column(Text, default="[]")
    requirement = Column(Text, nullable=False)
    acceptance_criteria = Column(Text, default="[]")
    security_impact = Column(Text, default="")
    test_method = Column(String(256), default="")
    failure_behavior = Column(String(256), default="")
    rollback_strategy = Column(Text, default="")
    evidence_ids = Column(Text, default="[]")
    reviewer = Column(String(128), default="")
    criticality = Column(String(8), default="P1", index=True)
    gate = Column(String(32), default="MVP")
    status = Column(String(16), default="NOT_STARTED", index=True)
    implementation_version = Column(String(64), default="")
    implementation_pass = Column(Boolean, default=False)
    automated_test_pass = Column(Boolean, default=False)
    security_test_pass = Column(Boolean, default=False)
    evidence_valid = Column(Boolean, default=False)
    independent_reviewer_valid = Column(Boolean, default=False)
    residual_risk_accepted = Column(Boolean, default=False)
    dependency_check_pass = Column(Boolean, default=False)
    rollback_test_pass = Column(Boolean, default=False)
    drift_detected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow)
