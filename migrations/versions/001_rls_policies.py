"""Enable RLS on orders table"""

from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Enable RLS
    op.execute("ALTER TABLE orders ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE orders FORCE ROW LEVEL SECURITY;")
    
    # Create policy
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON orders
        USING (tenant_id = current_setting('app.current_tenant')::text)
        WITH CHECK (tenant_id = current_setting('app.current_tenant')::text);
    """)
    
    # Create function untuk set tenant context
    op.execute("""
        CREATE OR REPLACE FUNCTION app.set_tenant(tenant_id text)
        RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.current_tenant', tenant_id, false);
        END;
        $$ LANGUAGE plpgsql;
    """)

def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON orders;")
    op.execute("ALTER TABLE orders DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP FUNCTION IF EXISTS app.set_tenant(text);")
