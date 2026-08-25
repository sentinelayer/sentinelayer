"""initial schema"""

from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'orders',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_orders_user_id', 'orders', ['user_id'])
    op.create_index('ix_orders_tenant_id', 'orders', ['tenant_id'])
    
    op.execute("ALTER TABLE orders ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE orders FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON orders
        USING (tenant_id = current_setting('app.current_tenant')::text)
        WITH CHECK (tenant_id = current_setting('app.current_tenant')::text);
    """)
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
    op.drop_table('orders')
