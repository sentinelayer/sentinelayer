"""Add durable authentication session registry.

Revision ID: 0018
Revises: 0017
"""
from alembic import op
import sqlalchemy as sa

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("token_id", sa.String(128), nullable=False, unique=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoke_reason", sa.String(256), nullable=True),
    )
    for name in ("token_id", "user_id", "tenant_id", "expires_at", "revoked_at"):
        op.create_index(f"ix_auth_sessions_{name}", "auth_sessions", [name])
    op.execute("ALTER TABLE auth_sessions ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY auth_sessions_tenant_isolation ON auth_sessions
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
    """)


def downgrade():
    op.execute("DROP POLICY IF EXISTS auth_sessions_tenant_isolation ON auth_sessions")
    op.execute("ALTER TABLE auth_sessions DISABLE ROW LEVEL SECURITY")
    for name in ("revoked_at", "expires_at", "tenant_id", "user_id", "token_id"):
        op.drop_index(f"ix_auth_sessions_{name}", table_name="auth_sessions")
    op.drop_table("auth_sessions")
