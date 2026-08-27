"""Persist schema, residency, and webhook configuration.

Revision ID: 0012
Revises: 0011
"""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "schema_records",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("schema_id", sa.String(128), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("schema_body", sa.Text(), nullable=False),
        sa.Column("hash_value", sa.String(64), nullable=False),
        sa.Column("registered_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("tenant_id", "schema_id", "version", name="uq_schema_tenant_id_version"),
    )
    op.create_index("ix_schema_records_tenant_id", "schema_records", ["tenant_id"])
    op.create_index("ix_schema_records_schema_id", "schema_records", ["schema_id"])
    op.create_table(
        "residency_rules",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("data_type", sa.String(128), nullable=False),
        sa.Column("primary_region", sa.String(64), nullable=False),
        sa.Column("backup_region", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_residency_rules_tenant_id", "residency_rules", ["tenant_id"])
    op.create_index("ix_residency_rules_data_type", "residency_rules", ["data_type"])
    op.create_table(
        "webhook_registrations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("events", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("secret_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_webhook_registrations_tenant_id", "webhook_registrations", ["tenant_id"])
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("webhook_id", sa.String(), sa.ForeignKey("webhook_registrations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("response_code", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_webhook_deliveries_tenant_id", "webhook_deliveries", ["tenant_id"])
    op.create_index("ix_webhook_deliveries_webhook_id", "webhook_deliveries", ["webhook_id"])


def downgrade():
    op.drop_index("ix_webhook_deliveries_webhook_id", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_tenant_id", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
    op.drop_index("ix_webhook_registrations_tenant_id", table_name="webhook_registrations")
    op.drop_table("webhook_registrations")
    op.drop_index("ix_residency_rules_data_type", table_name="residency_rules")
    op.drop_index("ix_residency_rules_tenant_id", table_name="residency_rules")
    op.drop_table("residency_rules")
    op.drop_index("ix_schema_records_schema_id", table_name="schema_records")
    op.drop_index("ix_schema_records_tenant_id", table_name="schema_records")
    op.drop_table("schema_records")
