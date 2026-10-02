"""Protect tenant directory reads and writes for the non-owner runtime role."""
from alembic import op

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY tenants_tenant_isolation ON tenants
        USING (id = current_setting('app.tenant_id', true))
        WITH CHECK (id = current_setting('app.tenant_id', true))""")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenants_tenant_isolation ON tenants")
    op.execute("ALTER TABLE tenants DISABLE ROW LEVEL SECURITY")
