"""Persist tenant alerts.

Revision ID: 0011
Revises: 0010
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source", sa.String(128), nullable=False, server_default="system"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", sa.String(), nullable=True),
    )
    for name in ("tenant_id", "severity", "status", "created_at"):
        op.create_index(f"ix_alerts_{name}", "alerts", [name])


def downgrade():
    for name in ("created_at", "status", "severity", "tenant_id"):
        op.drop_index(f"ix_alerts_{name}", table_name="alerts")
    op.drop_table("alerts")
