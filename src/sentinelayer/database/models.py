from sqlalchemy import Column, String, Boolean, DateTime, Float, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from src.sentinelayer.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    tenant_id = Column(UUID(as_uuid=True), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = "applications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Policy(Base):
    __tablename__ = "policies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"))
    rules = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    severity = Column(String)
    description = Column(String)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

class MFA(Base):
    __tablename__ = "mfa"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    secret = Column(String)
    enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class BreakGlassAccess(Base):
    __tablename__ = "breakglass"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reason = Column(String)
    status = Column(String, default="PENDING")
    requested_at = Column(String)
    approved_by = Column(String, nullable=True)
    approved_at = Column(String, nullable=True)
    expires_at = Column(String)
    duration_hours = Column(Integer, default=1)
    revoked_at = Column(String, nullable=True)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

class OffboardingRequest(Base):
    __tablename__ = "offboarding"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    reason = Column(String)
    status = Column(String, default="ONBOARDING")
    started_at = Column(String)
    soft_delete_at = Column(String)
    hard_delete_at = Column(String)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    price = Column(Float)
    status = Column(String, default="ACTIVE")

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    amount = Column(Float)
    paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Requirement(Base):
    __tablename__ = "requirements"
    id = Column(String, primary_key=True)
    implementation_status = Column(String, default="NOT_STARTED")
    test_count = Column(Integer, default=0)
    coverage = Column(Float, default=0.0)
    evidence_valid = Column(Boolean, default=False)
    reviewer_approved = Column(Boolean, default=False)
    config_drift = Column(Boolean, default=False)
    criticality = Column(String, default="P1")

class GateResult(Base):
    __tablename__ = "gate_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(String)
    status = Column(String)
    checks = Column(JSON)
    evaluated_at = Column(String)

class ReviewRequest(Base):
    __tablename__ = "reviews"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    change_id = Column(String)
    severity = Column(String)
    description = Column(String)
    status = Column(String, default="PENDING")
    requested_at = Column(String)
    due_at = Column(String)
    approved_at = Column(String, nullable=True)
    rejected_at = Column(String, nullable=True)
    rejection_reason = Column(String, nullable=True)
    notes = Column(String, nullable=True)

class ReviewLog(Base):
    __tablename__ = "review_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String)
    description = Column(String)
    severity = Column(String)
    logged_at = Column(String)
    review_deadline = Column(String)

class DRPlan(Base):
    __tablename__ = "dr_plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(String)
    status = Column(String)
    rto = Column(Integer)
    rpo = Column(Integer)
    backup_frequency_hours = Column(Integer)
    created_at = Column(String)
    updated_at = Column(String)

class DRTest(Base):
    __tablename__ = "dr_tests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("dr_plans.id"))
    started_at = Column(String)
    completed_at = Column(String, nullable=True)
    status = Column(String)
    result = Column(JSON, nullable=True)

class SLAMetric(Base):
    __tablename__ = "sla_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    value = Column(Float)
    target = Column(JSON)
    status = Column(String)
    recorded_at = Column(String)

class CustomerActivity(Base):
    __tablename__ = "customer_activities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    activity_type = Column(String)
    data = Column(JSON)
    occurred_at = Column(String)

class CostEntry(Base):
    __tablename__ = "costs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String)
    amount = Column(Float)
    description = Column(String)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    timestamp = Column(String)

class BudgetItem(Base):
    __tablename__ = "budget"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String)
    allocated = Column(Float)
    spent = Column(Float)
    period = Column(String)

class DriftEntry(Base):
    __tablename__ = "drifts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_type = Column(String)
    expected = Column(JSON)
    actual = Column(JSON)
    detected_at = Column(String)
    status = Column(String)

class BusFactorEntry(Base):
    __tablename__ = "bus_factor"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String)
    context = Column(JSON)
    timestamp = Column(String)

class ControlEvidence(Base):
    __tablename__ = "control_evidence"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(String)
    control_id = Column(String)
    artifact = Column(String)
    hash_value = Column(String, nullable=True)
    status = Column(String)
    recorded_at = Column(String)
    verified_at = Column(String, nullable=True)

class DataResidencyRule(Base):
    __tablename__ = "residency_rules"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_type = Column(String)
    primary_region = Column(String)
    backup_region = Column(String)
    allowed_regions = Column(JSON)
