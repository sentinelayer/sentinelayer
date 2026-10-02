"""Track registered gateway policy receipts with tenant isolation."""
from alembic import op
import sqlalchemy as sa

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("gateway_policy_deliveries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("gateway_id", sa.String(64), nullable=False),
        sa.Column("policy_id", sa.String(), sa.ForeignKey("policies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_user_id", sa.String(), nullable=False),
        sa.Column("reported_version", sa.Integer(), nullable=True),
        sa.Column("issued_at", sa.BigInteger(), nullable=True),
        sa.Column("expires_at", sa.BigInteger(), nullable=True),
        sa.Column("signing_key_id", sa.String(128), nullable=True),
        sa.Column("reported_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("tenant_id", "gateway_id", name="uq_gateway_delivery_tenant_gateway"))
    op.create_index("ix_gateway_policy_deliveries_tenant_id", "gateway_policy_deliveries", ["tenant_id"])
    op.create_index("ix_gateway_policy_deliveries_policy_id", "gateway_policy_deliveries", ["policy_id"])
    op.execute("ALTER TABLE gateway_policy_deliveries ENABLE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY gateway_policy_deliveries_tenant_isolation ON gateway_policy_deliveries
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))""")


def downgrade():
    op.drop_table("gateway_policy_deliveries")
