import sqlalchemy as sa
from alembic import op

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime()),
    )

    op.create_table(
        'applications',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String()),
        sa.Column('created_at', sa.DateTime()),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('tenant_id', sa.String()),
        sa.Column('created_at', sa.DateTime()),
    )

    op.create_table(
        'policies',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('rules', sa.String(), nullable=False),
        sa.Column('application_id', sa.String()),
        sa.Column('created_at', sa.DateTime()),
    )

    op.create_table(
        'incidents',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('status', sa.String(), default='open'),
        sa.Column('tenant_id', sa.String()),
        sa.Column('created_at', sa.DateTime()),
    )

    op.create_table(
        'evidence',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('artifact', sa.String(), nullable=False),
        sa.Column('requirement_id', sa.String(), nullable=False),
        sa.Column('control_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), default='CREATED'),
        sa.Column('created_at', sa.DateTime()),
    )

def downgrade():
    op.drop_table('evidence')
    op.drop_table('incidents')
    op.drop_table('policies')
    op.drop_table('users')
    op.drop_table('applications')
    op.drop_table('tenants')
