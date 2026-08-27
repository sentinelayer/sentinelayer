"""Enable RLS on all tenant-scoped tables introduced after the initial RLS migration.

Revision ID: 0014
Revises: 0013
"""
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    DO $$
    DECLARE
      table_name text;
    BEGIN
      FOREACH table_name IN ARRAY ARRAY[
        'policy_versions', 'high_risk_actions', 'breakglass_sessions',
        'audit_events', 'runtime_events', 'threat_intel_indicators',
        'offboarding_requests', 'alerts', 'schema_records',
        'residency_rules', 'webhook_registrations', 'webhook_deliveries',
        'configuration_entries', 'evidence'
      ] LOOP
        IF to_regclass(table_name) IS NOT NULL THEN
          EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);
          EXECUTE format('DROP POLICY IF EXISTS %I ON %I', table_name || '_tenant_isolation', table_name);
          EXECUTE format(
            'CREATE POLICY %I ON %I USING (tenant_id = current_setting(''app.tenant_id'', true)) WITH CHECK (tenant_id = current_setting(''app.tenant_id'', true))',
            table_name || '_tenant_isolation', table_name
          );
        END IF;
      END LOOP;
    END $$;
    """)


def downgrade():
    op.execute("""
    DO $$
    DECLARE
      table_name text;
    BEGIN
      FOREACH table_name IN ARRAY ARRAY[
        'policy_versions', 'high_risk_actions', 'breakglass_sessions',
        'audit_events', 'runtime_events', 'threat_intel_indicators',
        'offboarding_requests', 'alerts', 'schema_records',
        'residency_rules', 'webhook_registrations', 'webhook_deliveries',
        'configuration_entries', 'evidence'
      ] LOOP
        IF to_regclass(table_name) IS NOT NULL THEN
          EXECUTE format('DROP POLICY IF EXISTS %I ON %I', table_name || '_tenant_isolation', table_name);
          EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY', table_name);
        END IF;
      END LOOP;
    END $$;
    """)
