"""Enable RLS on orders table"""

from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
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

def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON orders;")
    op.execute("ALTER TABLE orders DISABLE ROW LEVEL SECURITY;")
