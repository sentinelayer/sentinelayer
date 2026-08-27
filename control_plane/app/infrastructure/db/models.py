import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

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
    current_version = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow)


class PolicyVersion(Base):
    __tablename__ = "policy_versions"
    __table_args__ = (UniqueConstraint("policy_id", "version", name="uq_policy_versions_policy_version"),)

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id = Column(String, ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    rules = Column(Text, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    superseded_at = Column(DateTime, nullable=True)
    rollback_of_version = Column(Integer, nullable=True)


class HighRiskActionRecord(Base):
    __tablename__ = "high_risk_actions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    action = Column(String(64), nullable=False)
    reason = Column(Text, nullable=False)
    requested_by = Column(String, ForeignKey("users.id"), nullable=False)
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)
    rejected_by = Column(String, ForeignKey("users.id"), nullable=True)
    status = Column(String(32), nullable=False, default="PENDING_APPROVAL", index=True)
    requested_at = Column(DateTime, default=_utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)


class BreakGlassSession(Base):
    __tablename__ = "breakglass_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    requested_by = Column(String, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="PENDING", index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    actor_id = Column(String, nullable=True)
    action = Column(String(128), nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=True)
    detail = Column(Text, nullable=False, default="{}")
    previous_hash = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=False, unique=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)


class ConfigurationEntry(Base):
    __tablename__ = "configuration_entries"
    __table_args__ = (UniqueConstraint("tenant_id", "key", name="uq_configuration_tenant_key"),)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    key = Column(String(128), nullable=False)
    value = Column(Text, nullable=False)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class SchemaRecord(Base):
    __tablename__ = "schema_records"
    __table_args__ = (UniqueConstraint("tenant_id", "schema_id", "version", name="uq_schema_tenant_id_version"),)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    schema_id = Column(String(128), nullable=False, index=True)
    version = Column(String(64), nullable=False)
    schema_body = Column(Text, nullable=False)
    hash_value = Column(String(64), nullable=False)
    registered_at = Column(DateTime, default=_utcnow, nullable=False)


class ResidencyRuleRecord(Base):
    __tablename__ = "residency_rules"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    data_type = Column(String(128), nullable=False, index=True)
    primary_region = Column(String(64), nullable=False)
    backup_region = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class WebhookRegistration(Base):
    __tablename__ = "webhook_registrations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    url = Column(String(2048), nullable=False)
    events = Column(Text, nullable=False, default="[]")
    secret_hash = Column(String(64), nullable=False)
    secret_ciphertext = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    webhook_id = Column(String, ForeignKey("webhook_registrations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(128), nullable=False)
    payload = Column(Text, nullable=False, default="{}")
    status = Column(String(32), nullable=False, default="queued")
    response_code = Column(Integer, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime, nullable=True, index=True)
    last_error = Column(Text, nullable=True)
    last_signature = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    severity = Column(String(16), nullable=False, index=True)
    message = Column(Text, nullable=False)
    source = Column(String(128), nullable=False, default="system")
    status = Column(String(16), nullable=False, default="active", index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)


class ThreatIntelIndicator(Base):
    __tablename__ = "threat_intel_indicators"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True, index=True)
    indicator_type = Column(String(32), nullable=False, index=True)
    value = Column(String(512), nullable=False, index=True)
    severity = Column(String(16), nullable=False, default="medium")
    source = Column(String(128), nullable=False)
    tags = Column(Text, nullable=False, default="[]")
    confidence = Column(Integer, nullable=False, default=50)
    reliability = Column(Integer, nullable=False, default=50)
    first_seen = Column(DateTime, default=_utcnow, nullable=False)
    last_seen = Column(DateTime, default=_utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, nullable=False)


class RuntimeEvent(Base):
    __tablename__ = "runtime_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    source = Column(String(128), nullable=False, default="system")
    data = Column(Text, nullable=False, default="{}")
    severity = Column(String(16), nullable=True, index=True)
    risk_score = Column(Integer, nullable=True, index=True)
    outcome = Column(String(32), nullable=True, index=True)
    occurred_at = Column(DateTime, default=_utcnow, nullable=False, index=True)


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
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True, index=True)
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
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
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


class ApiKeyRecord(Base):
    __tablename__ = "api_keys"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=False)
    key_prefix = Column(String(16), nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)
    revoked_at = Column(DateTime, nullable=True, index=True)
    last_used_at = Column(DateTime, nullable=True)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    token_id = Column(String(128), unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True, index=True)
    revoke_reason = Column(String(256), nullable=True)


class ApplicabilityDecision(Base):
    __tablename__ = "applicability_decisions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    customer_type = Column(String(64), nullable=False)
    industry = Column(String(128), nullable=False)
    data_type = Column(String(128), nullable=False)
    region = Column(String(64), nullable=False)
    result = Column(Text, nullable=False, default="{}")
    evaluated_by = Column(String, nullable=True)
    evaluated_at = Column(DateTime, default=_utcnow, nullable=False, index=True)


class GateEvaluation(Base):
    __tablename__ = "gate_evaluations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    requirement_id = Column(String(64), ForeignKey("requirements.id"), nullable=False, index=True)
    evaluator_id = Column(String, nullable=True)
    status = Column(String(16), nullable=False, index=True)
    checks = Column(Text, nullable=False, default="[]")
    all_pass = Column(Boolean, nullable=False, default=False)
    result_hash = Column(String(64), nullable=False)
    evaluated_at = Column(DateTime, default=_utcnow, nullable=False, index=True)


class OffboardingRequest(Base):
    __tablename__ = "offboarding_requests"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    requested_by = Column(String, ForeignKey("users.id"), nullable=True)
    mode = Column(String(16), nullable=False, default="soft")
    status = Column(String(32), nullable=False, default="REQUESTED", index=True)
    before_hash = Column(String(64), nullable=True)
    after_hash = Column(String(64), nullable=True)
    requested_at = Column(DateTime, default=_utcnow, nullable=False)
    hard_delete_at = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
