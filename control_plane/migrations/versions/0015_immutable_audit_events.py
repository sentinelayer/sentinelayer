"""Make audit events append-only in PostgreSQL.

Revision ID: 0015
Revises: 0014
"""
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_audit_event_mutation() RETURNS trigger AS $$
    BEGIN
      RAISE EXCEPTION 'audit_events are append-only';
    END;
    $$ LANGUAGE plpgsql;
    """)
    op.execute("""
    DROP TRIGGER IF EXISTS audit_events_no_update ON audit_events;
    CREATE TRIGGER audit_events_no_update
      BEFORE UPDATE OR DELETE ON audit_events
      FOR EACH ROW EXECUTE FUNCTION prevent_audit_event_mutation();
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS audit_events_no_update ON audit_events")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_event_mutation()")
