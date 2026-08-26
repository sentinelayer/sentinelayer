"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-08-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('tenant_id', UUID()),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'])

    op.create_table(
        'tenants',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'applications',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('tenant_id', UUID()),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'policies',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('application_id', UUID()),
        sa.Column('rules', sa.JSON(), default={}),
        sa.Column('created_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'incidents',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('tenant_id', UUID()),
        sa.Column('severity', sa.String()),
        sa.Column('description', sa.String()),
        sa.Column('status', sa.String(), default='open'),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'mfa',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('user_id', UUID()),
        sa.Column('secret', sa.String()),
        sa.Column('enabled', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'breakglass',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('user_id', UUID()),
        sa.Column('reason', sa.String()),
        sa.Column('status', sa.String(), default='PENDING'),
        sa.Column('requested_at', sa.String()),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('approved_at', sa.String(), nullable=True),
        sa.Column('expires_at', sa.String()),
        sa.Column('duration_hours', sa.Integer(), default=1),
        sa.Column('revoked_at', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'customers',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('name', sa.String()),
        sa.Column('status', sa.String(), default='ACTIVE'),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'offboarding',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('customer_id', UUID()),
        sa.Column('reason', sa.String()),
        sa.Column('status', sa.String(), default='ONBOARDING'),
        sa.Column('started_at', sa.String()),
        sa.Column('soft_delete_at', sa.String()),
        sa.Column('hard_delete_at', sa.String()),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'subscriptions',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('customer_id', UUID()),
        sa.Column('price', sa.Float()),
        sa.Column('status', sa.String(), default='ACTIVE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'invoices',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('customer_id', UUID()),
        sa.Column('amount', sa.Float()),
        sa.Column('paid', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'requirements',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('implementation_status', sa.String(), default='NOT_STARTED'),
        sa.Column('test_count', sa.Integer(), default=0),
        sa.Column('coverage', sa.Float(), default=0.0),
        sa.Column('evidence_valid', sa.Boolean(), default=False),
        sa.Column('reviewer_approved', sa.Boolean(), default=False),
        sa.Column('config_drift', sa.Boolean(), default=False),
        sa.Column('criticality', sa.String(), default='P1')
    )

    op.create_table(
        'gate_results',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('requirement_id', sa.String()),
        sa.Column('status', sa.String()),
        sa.Column('checks', sa.JSON()),
        sa.Column('evaluated_at', sa.String())
    )

    op.create_table(
        'reviews',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('change_id', sa.String()),
        sa.Column('severity', sa.String()),
        sa.Column('description', sa.String()),
        sa.Column('status', sa.String(), default='PENDING'),
        sa.Column('requested_at', sa.String()),
        sa.Column('due_at', sa.String()),
        sa.Column('approved_at', sa.String(), nullable=True),
        sa.Column('rejected_at', sa.String(), nullable=True),
        sa.Column('rejection_reason', sa.String(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True)
    )

    op.create_table(
        'review_logs',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('action', sa.String()),
        sa.Column('description', sa.String()),
        sa.Column('severity', sa.String()),
        sa.Column('logged_at', sa.String()),
        sa.Column('review_deadline', sa.String())
    )

    op.create_table(
        'dr_plans',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('name', sa.String()),
        sa.Column('description', sa.String()),
        sa.Column('status', sa.String()),
        sa.Column('rto', sa.Integer()),
        sa.Column('rpo', sa.Integer()),
        sa.Column('backup_frequency_hours', sa.Integer()),
        sa.Column('created_at', sa.String()),
        sa.Column('updated_at', sa.String())
    )

    op.create_table(
        'dr_tests',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('plan_id', UUID()),
        sa.Column('started_at', sa.String()),
        sa.Column('completed_at', sa.String(), nullable=True),
        sa.Column('status', sa.String()),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['dr_plans.id'])
    )

    op.create_table(
        'sla_metrics',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('name', sa.String()),
        sa.Column('value', sa.Float()),
        sa.Column('target', sa.JSON()),
        sa.Column('status', sa.String()),
        sa.Column('recorded_at', sa.String())
    )

    op.create_table(
        'customer_activities',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('customer_id', UUID()),
        sa.Column('activity_type', sa.String()),
        sa.Column('data', sa.JSON()),
        sa.Column('occurred_at', sa.String()),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'])
    )

    op.create_table(
        'costs',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('category', sa.String()),
        sa.Column('amount', sa.Float()),
        sa.Column('description', sa.String()),
        sa.Column('customer_id', UUID(), nullable=True),
        sa.Column('timestamp', sa.String()),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'])
    )

    op.create_table(
        'budget',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('category', sa.String()),
        sa.Column('allocated', sa.Float()),
        sa.Column('spent', sa.Float()),
        sa.Column('period', sa.String())
    )

    op.create_table(
        'drifts',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('resource_type', sa.String()),
        sa.Column('expected', sa.JSON()),
        sa.Column('actual', sa.JSON()),
        sa.Column('detected_at', sa.String()),
        sa.Column('status', sa.String())
    )

    op.create_table(
        'bus_factor',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('action', sa.String()),
        sa.Column('context', sa.JSON()),
        sa.Column('timestamp', sa.String())
    )

    op.create_table(
        'control_evidence',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('requirement_id', sa.String()),
        sa.Column('control_id', sa.String()),
        sa.Column('artifact', sa.String()),
        sa.Column('hash_value', sa.String(), nullable=True),
        sa.Column('status', sa.String()),
        sa.Column('recorded_at', sa.String()),
        sa.Column('verified_at', sa.String(), nullable=True)
    )

    op.create_table(
        'residency_rules',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('data_type', sa.String()),
        sa.Column('primary_region', sa.String()),
        sa.Column('backup_region', sa.String()),
        sa.Column('allowed_regions', sa.JSON())
    )

def downgrade():
    op.drop_table('residency_rules')
    op.drop_table('control_evidence')
    op.drop_table('bus_factor')
    op.drop_table('drifts')
    op.drop_table('budget')
    op.drop_table('costs')
    op.drop_table('customer_activities')
    op.drop_table('sla_metrics')
    op.drop_table('dr_tests')
    op.drop_table('dr_plans')
    op.drop_table('review_logs')
    op.drop_table('reviews')
    op.drop_table('gate_results')
    op.drop_table('requirements')
    op.drop_table('invoices')
    op.drop_table('subscriptions')
    op.drop_table('offboarding')
    op.drop_table('customers')
    op.drop_table('breakglass')
    op.drop_table('mfa')
    op.drop_table('incidents')
    op.drop_table('policies')
    op.drop_table('applications')
    op.drop_table('tenants')
    op.drop_table('users')
