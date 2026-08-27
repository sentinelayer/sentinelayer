"""Add tenant ownership to evidence.

Revision ID: 0010
Revises: 0009
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("evidence", sa.Column("tenant_id", sa.String(), nullable=True))
    op.create_index("ix_evidence_tenant_id", "evidence", ["tenant_id"])


def downgrade():
    op.drop_index("ix_evidence_tenant_id", table_name="evidence")
    op.drop_column("evidence", "tenant_id")
