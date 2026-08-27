"""Add durable execution metadata to high-risk actions.

Revision ID: 0025
Revises: 0024
"""
from alembic import op
import sqlalchemy as sa

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("high_risk_actions", sa.Column("executed_by", sa.String(), nullable=True))
    op.add_column("high_risk_actions", sa.Column("executed_at", sa.DateTime(), nullable=True))
    op.create_index("ix_high_risk_actions_executed_at", "high_risk_actions", ["executed_at"])


def downgrade():
    op.drop_index("ix_high_risk_actions_executed_at", table_name="high_risk_actions")
    op.drop_column("high_risk_actions", "executed_at")
    op.drop_column("high_risk_actions", "executed_by")
