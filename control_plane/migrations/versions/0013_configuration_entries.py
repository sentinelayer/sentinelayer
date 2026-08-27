"""Persist tenant configuration overrides.

Revision ID: 0013
Revises: 0012
"""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "configuration_entries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("tenant_id", "key", name="uq_configuration_tenant_key"),
    )
    op.create_index("ix_configuration_entries_tenant_id", "configuration_entries", ["tenant_id"])


def downgrade():
    op.drop_index("ix_configuration_entries_tenant_id", table_name="configuration_entries")
    op.drop_table("configuration_entries")
