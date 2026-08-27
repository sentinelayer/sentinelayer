"""Persist compliance applicability decisions.

Revision ID: 0017
Revises: 0016
"""
from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "applicability_decisions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("customer_type", sa.String(64), nullable=False),
        sa.Column("industry", sa.String(128), nullable=False),
        sa.Column("data_type", sa.String(128), nullable=False),
        sa.Column("region", sa.String(64), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("evaluated_by", sa.String(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
    )
    for name in ("tenant_id", "evaluated_at"):
        op.create_index(f"ix_applicability_decisions_{name}", "applicability_decisions", [name])
    op.execute("ALTER TABLE applicability_decisions ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY applicability_decisions_tenant_isolation ON applicability_decisions
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
    """)


def downgrade():
    op.execute("DROP POLICY IF EXISTS applicability_decisions_tenant_isolation ON applicability_decisions")
    op.execute("ALTER TABLE applicability_decisions DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_applicability_decisions_evaluated_at", table_name="applicability_decisions")
    op.drop_index("ix_applicability_decisions_tenant_id", table_name="applicability_decisions")
    op.drop_table("applicability_decisions")
