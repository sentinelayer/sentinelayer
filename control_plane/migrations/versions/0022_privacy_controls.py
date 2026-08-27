"""Add privacy export requests and legal holds.

Revision ID: 0022
Revises: 0021
"""
from alembic import op
import sqlalchemy as sa

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "legal_holds",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("released_at", sa.DateTime(), nullable=True),
        sa.Column("released_by", sa.String(), nullable=True),
    )
    op.create_table(
        "privacy_export_requests",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("requested_by", sa.String(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("artifact_path", sa.Text(), nullable=True),
        sa.Column("artifact_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_legal_holds_tenant_id", "legal_holds", ["tenant_id"])
    op.create_index("ix_legal_holds_status", "legal_holds", ["status"])
    op.create_index("ix_privacy_export_requests_tenant_id", "privacy_export_requests", ["tenant_id"])
    op.create_index("ix_privacy_export_requests_status", "privacy_export_requests", ["status"])
    op.execute("ALTER TABLE legal_holds ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE privacy_export_requests ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY legal_holds_tenant_isolation ON legal_holds
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
    """)
    op.execute("""
        CREATE POLICY privacy_export_requests_tenant_isolation ON privacy_export_requests
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
    """)


def downgrade():
    op.execute("DROP POLICY IF EXISTS privacy_export_requests_tenant_isolation ON privacy_export_requests")
    op.execute("ALTER TABLE privacy_export_requests DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_privacy_export_requests_status", table_name="privacy_export_requests")
    op.drop_index("ix_privacy_export_requests_tenant_id", table_name="privacy_export_requests")
    op.drop_table("privacy_export_requests")
    op.execute("DROP POLICY IF EXISTS legal_holds_tenant_isolation ON legal_holds")
    op.execute("ALTER TABLE legal_holds DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_legal_holds_status", table_name="legal_holds")
    op.drop_index("ix_legal_holds_tenant_id", table_name="legal_holds")
    op.drop_table("legal_holds")
