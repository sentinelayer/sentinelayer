"""Add tenant_id to policies for hard tenant isolation

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("policies", sa.Column("tenant_id", sa.String(), nullable=True))
    op.create_index("ix_policies_tenant_id", "policies", ["tenant_id"])
    # best-effort backfill from applications
    op.execute(
        """
        UPDATE policies AS p
        SET tenant_id = a.tenant_id
        FROM applications AS a
        WHERE p.application_id = a.id AND p.tenant_id IS NULL
        """
    )


def downgrade():
    op.drop_index("ix_policies_tenant_id", table_name="policies")
    op.drop_column("policies", "tenant_id")
