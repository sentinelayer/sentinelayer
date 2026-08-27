"""Add durable signatures to policy versions.

Revision ID: 0024
Revises: 0023
"""
from alembic import op
import sqlalchemy as sa

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("policy_versions", sa.Column("signature", sa.Text(), nullable=True))
    op.add_column("policy_versions", sa.Column("signing_key_id", sa.String(128), nullable=True))
    op.create_index("ix_policy_versions_signing_key_id", "policy_versions", ["signing_key_id"])


def downgrade():
    op.drop_index("ix_policy_versions_signing_key_id", table_name="policy_versions")
    op.drop_column("policy_versions", "signing_key_id")
    op.drop_column("policy_versions", "signature")
