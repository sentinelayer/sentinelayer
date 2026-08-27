"""Persist threat intelligence indicators.

Revision ID: 0009
Revises: 0008
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "threat_intel_indicators",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("indicator_type", sa.String(32), nullable=False),
        sa.Column("value", sa.String(512), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("source", sa.String(128), nullable=False),
        sa.Column("tags", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("reliability", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("first_seen", sa.DateTime(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for name in ("tenant_id", "indicator_type", "value", "expires_at"):
        op.create_index(f"ix_threat_intel_indicators_{name}", "threat_intel_indicators", [name])


def downgrade():
    for name in ("expires_at", "value", "indicator_type", "tenant_id"):
        op.drop_index(f"ix_threat_intel_indicators_{name}", table_name="threat_intel_indicators")
    op.drop_table("threat_intel_indicators")
