"""Persist policy versions, privileged actions, and audit events.

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "policies",
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "policy_versions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("policy_id", sa.String(), sa.ForeignKey("policies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("rules", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("superseded_at", sa.DateTime(), nullable=True),
        sa.Column("rollback_of_version", sa.Integer(), nullable=True),
        sa.UniqueConstraint("policy_id", "version", name="uq_policy_versions_policy_version"),
    )
    op.create_index("ix_policy_versions_policy_id", "policy_versions", ["policy_id"])
    op.create_index("ix_policy_versions_tenant_id", "policy_versions", ["tenant_id"])

    op.create_table(
        "high_risk_actions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("requested_by", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approved_by", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("rejected_by", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING_APPROVAL"),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_high_risk_actions_tenant_id", "high_risk_actions", ["tenant_id"])
    op.create_index("ix_high_risk_actions_status", "high_risk_actions", ["status"])

    op.create_table(
        "breakglass_sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("requested_by", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("approved_by", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_breakglass_sessions_tenant_id", "breakglass_sessions", ["tenant_id"])
    op.create_index("ix_breakglass_sessions_status", "breakglass_sessions", ["status"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("actor_id", sa.String(), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(128), nullable=True),
        sa.Column("detail", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("previous_hash", sa.String(64), nullable=True),
        sa.Column("event_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_events_tenant_id", "audit_events", ["tenant_id"])
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])


def downgrade():
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_index("ix_audit_events_tenant_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_breakglass_sessions_status", table_name="breakglass_sessions")
    op.drop_index("ix_breakglass_sessions_tenant_id", table_name="breakglass_sessions")
    op.drop_table("breakglass_sessions")
    op.drop_index("ix_high_risk_actions_status", table_name="high_risk_actions")
    op.drop_index("ix_high_risk_actions_tenant_id", table_name="high_risk_actions")
    op.drop_table("high_risk_actions")
    op.drop_index("ix_policy_versions_tenant_id", table_name="policy_versions")
    op.drop_index("ix_policy_versions_policy_id", table_name="policy_versions")
    op.drop_table("policy_versions")
    op.drop_column("policies", "current_version")
