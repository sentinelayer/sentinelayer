"""Persist offboarding lifecycle records.

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "offboarding_requests",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("requested_by", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("mode", sa.String(16), nullable=False, server_default="soft"),
        sa.Column("status", sa.String(32), nullable=False, server_default="REQUESTED"),
        sa.Column("before_hash", sa.String(64), nullable=True),
        sa.Column("after_hash", sa.String(64), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("hard_delete_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_offboarding_requests_tenant_id", "offboarding_requests", ["tenant_id"])
    op.create_index("ix_offboarding_requests_status", "offboarding_requests", ["status"])
    op.create_index("ix_offboarding_requests_hard_delete_at", "offboarding_requests", ["hard_delete_at"])


def downgrade():
    op.drop_index("ix_offboarding_requests_hard_delete_at", table_name="offboarding_requests")
    op.drop_index("ix_offboarding_requests_status", table_name="offboarding_requests")
    op.drop_index("ix_offboarding_requests_tenant_id", table_name="offboarding_requests")
    op.drop_table("offboarding_requests")
