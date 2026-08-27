"""Add durable webhook delivery security state.

Revision ID: 0020
Revises: 0019
"""
from alembic import op
import sqlalchemy as sa

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("webhook_registrations", sa.Column("secret_ciphertext", sa.Text(), nullable=True))
    op.add_column("webhook_deliveries", sa.Column("payload", sa.Text(), nullable=True))
    op.add_column("webhook_deliveries", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("webhook_deliveries", sa.Column("next_attempt_at", sa.DateTime(), nullable=True))
    op.add_column("webhook_deliveries", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("webhook_deliveries", sa.Column("last_signature", sa.String(128), nullable=True))
    op.execute("UPDATE webhook_deliveries SET payload = '{}' WHERE payload IS NULL")
    op.alter_column("webhook_deliveries", "payload", nullable=False, server_default="{}")
    op.create_index("ix_webhook_deliveries_next_attempt_at", "webhook_deliveries", ["next_attempt_at"])


def downgrade():
    op.drop_index("ix_webhook_deliveries_next_attempt_at", table_name="webhook_deliveries")
    op.drop_column("webhook_deliveries", "last_signature")
    op.drop_column("webhook_deliveries", "last_error")
    op.drop_column("webhook_deliveries", "next_attempt_at")
    op.drop_column("webhook_deliveries", "attempt_count")
    op.drop_column("webhook_deliveries", "payload")
    op.drop_column("webhook_registrations", "secret_ciphertext")
