"""Add durable one-use bootstrap admin grants.

Revision ID: 0023
Revises: 0022
"""
from alembic import op
import sqlalchemy as sa

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bootstrap_admin_grants",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("used_by", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_bootstrap_admin_grants_email", "bootstrap_admin_grants", ["email"])


def downgrade():
    op.drop_index("ix_bootstrap_admin_grants_email", table_name="bootstrap_admin_grants")
    op.drop_table("bootstrap_admin_grants")
