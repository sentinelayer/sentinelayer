"""Persist behavior baselines and risk decision evidence.

Revision ID: 0021
Revises: 0020
"""
from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def _enable_rls():
    op.execute("ALTER TABLE behavior_baselines ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE risk_calibrations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE risk_decisions ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY behavior_baselines_tenant_isolation ON behavior_baselines
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
    """)
    op.execute("""
        CREATE POLICY risk_calibrations_tenant_isolation ON risk_calibrations
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
    """)
    op.execute("""
        CREATE POLICY risk_decisions_tenant_isolation ON risk_decisions
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
    """)


def upgrade():
    op.create_table(
        "behavior_baselines",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("baseline_key", sa.String(256), nullable=False),
        sa.Column("baseline_type", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("stats", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "risk_calibrations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("factor", sa.Integer(), nullable=False),
        sa.Column("dataset_hash", sa.String(64), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("fp_rate", sa.Integer(), nullable=True),
        sa.Column("fn_rate", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "risk_decisions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("event_id", sa.String(), sa.ForeignKey("runtime_events.id"), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("factors", sa.Text(), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for table, columns in {
        "behavior_baselines": ("tenant_id", "baseline_key", "status"),
        "risk_calibrations": ("tenant_id", "status"),
        "risk_decisions": ("tenant_id", "event_id", "created_at"),
    }.items():
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column])
    _enable_rls()


def downgrade():
    op.execute("DROP POLICY IF EXISTS risk_decisions_tenant_isolation ON risk_decisions")
    op.execute("ALTER TABLE risk_decisions DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_risk_decisions_created_at", table_name="risk_decisions")
    op.drop_index("ix_risk_decisions_event_id", table_name="risk_decisions")
    op.drop_index("ix_risk_decisions_tenant_id", table_name="risk_decisions")
    op.drop_table("risk_decisions")
    op.execute("DROP POLICY IF EXISTS risk_calibrations_tenant_isolation ON risk_calibrations")
    op.execute("ALTER TABLE risk_calibrations DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_risk_calibrations_status", table_name="risk_calibrations")
    op.drop_index("ix_risk_calibrations_tenant_id", table_name="risk_calibrations")
    op.drop_table("risk_calibrations")
    op.execute("DROP POLICY IF EXISTS behavior_baselines_tenant_isolation ON behavior_baselines")
    op.execute("ALTER TABLE behavior_baselines DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_behavior_baselines_status", table_name="behavior_baselines")
    op.drop_index("ix_behavior_baselines_baseline_key", table_name="behavior_baselines")
    op.drop_index("ix_behavior_baselines_tenant_id", table_name="behavior_baselines")
    op.drop_table("behavior_baselines")
