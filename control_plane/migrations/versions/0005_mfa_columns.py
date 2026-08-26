"""add mfa columns to users

Revision ID: 0005
Revises: 0004
"""
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_secret VARCHAR")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_backup_codes TEXT")
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS environment VARCHAR DEFAULT 'production'")


def downgrade():
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS mfa_enabled")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS mfa_secret")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS mfa_backup_codes")
