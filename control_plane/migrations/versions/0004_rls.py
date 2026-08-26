"""Enable RLS on tenant tables

Revision ID: 0004
Revises: 0003
"""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    ALTER TABLE IF EXISTS applications ENABLE ROW LEVEL SECURITY;
    ALTER TABLE IF EXISTS policies ENABLE ROW LEVEL SECURITY;
    ALTER TABLE IF EXISTS incidents ENABLE ROW LEVEL SECURITY;
    ALTER TABLE IF EXISTS users ENABLE ROW LEVEL SECURITY;

    DROP POLICY IF EXISTS applications_tenant_isolation ON applications;
    CREATE POLICY applications_tenant_isolation ON applications
      USING (tenant_id = current_setting('app.tenant_id', true))
      WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

    DROP POLICY IF EXISTS policies_tenant_isolation ON policies;
    CREATE POLICY policies_tenant_isolation ON policies
      USING (tenant_id IS NULL OR tenant_id = current_setting('app.tenant_id', true))
      WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

    DROP POLICY IF EXISTS incidents_tenant_isolation ON incidents;
    CREATE POLICY incidents_tenant_isolation ON incidents
      USING (tenant_id = current_setting('app.tenant_id', true))
      WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

    DROP POLICY IF EXISTS users_tenant_isolation ON users;
    CREATE POLICY users_tenant_isolation ON users
      USING (tenant_id = current_setting('app.tenant_id', true))
      WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
    """)


def downgrade():
    op.execute("""
    DROP POLICY IF EXISTS applications_tenant_isolation ON applications;
    DROP POLICY IF EXISTS policies_tenant_isolation ON policies;
    DROP POLICY IF EXISTS incidents_tenant_isolation ON incidents;
    DROP POLICY IF EXISTS users_tenant_isolation ON users;
    ALTER TABLE IF EXISTS applications DISABLE ROW LEVEL SECURITY;
    ALTER TABLE IF EXISTS policies DISABLE ROW LEVEL SECURITY;
    ALTER TABLE IF EXISTS incidents DISABLE ROW LEVEL SECURITY;
    ALTER TABLE IF EXISTS users DISABLE ROW LEVEL SECURITY;
    """)
