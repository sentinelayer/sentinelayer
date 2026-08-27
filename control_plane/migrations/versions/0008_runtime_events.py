"""Persist runtime security events.

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "runtime_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("source", sa.String(128), nullable=False, server_default="system"),
        sa.Column("data", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("severity", sa.String(16), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("outcome", sa.String(32), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
    )
    for name, column in (("event_type", "event_type"), ("severity", "severity"),
                         ("risk_score", "risk_score"), ("outcome", "outcome"),
                         ("occurred_at", "occurred_at")):
        op.create_index(f"ix_runtime_events_{name}", "runtime_events", [column])
    op.create_index("ix_runtime_events_tenant_id", "runtime_events", ["tenant_id"])


def downgrade():
    for name in ("tenant_id", "occurred_at", "outcome", "risk_score", "severity", "event_type"):
        op.drop_index(f"ix_runtime_events_{name}", table_name="runtime_events")
    op.drop_table("runtime_events")
