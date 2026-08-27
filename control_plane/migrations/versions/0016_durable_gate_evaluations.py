"""Add tenant-scoped durable acceptance gate evaluations.

Revision ID: 0016
Revises: 0015
"""
from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade():
    # Nullable is intentional for upgrade safety; legacy rows require an explicit
    # tenant backfill before they can be evaluated by the API.
    op.add_column("requirements", sa.Column("tenant_id", sa.String(), nullable=True))
    op.create_index("ix_requirements_tenant_id", "requirements", ["tenant_id"])
    op.create_table(
        "gate_evaluations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("requirement_id", sa.String(64), sa.ForeignKey("requirements.id"), nullable=False),
        sa.Column("evaluator_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("checks", sa.Text(), nullable=False),
        sa.Column("all_pass", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("result_hash", sa.String(64), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
    )
    for name in ("tenant_id", "requirement_id", "status", "evaluated_at"):
        op.create_index(f"ix_gate_evaluations_{name}", "gate_evaluations", [name])
    op.execute("ALTER TABLE requirements ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS requirements_tenant_isolation ON requirements")
    op.execute("""
        CREATE POLICY requirements_tenant_isolation ON requirements
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
    """)
    op.execute("ALTER TABLE gate_evaluations ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY gate_evaluations_tenant_isolation ON gate_evaluations
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
    """)


def downgrade():
    op.execute("DROP POLICY IF EXISTS gate_evaluations_tenant_isolation ON gate_evaluations")
    op.execute("ALTER TABLE gate_evaluations DISABLE ROW LEVEL SECURITY")
    for name in ("evaluated_at", "status", "requirement_id", "tenant_id"):
        op.drop_index(f"ix_gate_evaluations_{name}", table_name="gate_evaluations")
    op.drop_table("gate_evaluations")
    op.execute("DROP POLICY IF EXISTS requirements_tenant_isolation ON requirements")
    op.execute("ALTER TABLE requirements DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_requirements_tenant_id", table_name="requirements")
    op.drop_column("requirements", "tenant_id")
