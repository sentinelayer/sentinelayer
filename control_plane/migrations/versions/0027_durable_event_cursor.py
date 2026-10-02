"""Give tenant events transactionally ordered, durable replay cursors."""
from alembic import op
import sqlalchemy as sa

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade():
    # Stop concurrent legacy writers while assigning historical cursors.
    op.execute("LOCK TABLE runtime_events IN ACCESS EXCLUSIVE MODE")
    op.add_column("runtime_events", sa.Column("sequence", sa.BigInteger(), nullable=True))
    op.execute("""WITH numbered AS (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY tenant_id ORDER BY occurred_at, id) AS seq
        FROM runtime_events
    ) UPDATE runtime_events SET sequence = numbered.seq FROM numbered
      WHERE runtime_events.id = numbered.id""")
    op.alter_column("runtime_events", "sequence", nullable=False)
    op.create_unique_constraint("uq_runtime_events_tenant_sequence", "runtime_events", ["tenant_id", "sequence"])
    op.create_table("tenant_event_offsets",
                    sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), primary_key=True),
                    sa.Column("last_sequence", sa.BigInteger(), nullable=False, server_default="0"))
    op.execute("""INSERT INTO tenant_event_offsets (tenant_id, last_sequence)
                  SELECT tenant_id, MAX(sequence) FROM runtime_events GROUP BY tenant_id""")
    op.execute("ALTER TABLE tenant_event_offsets ENABLE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY tenant_event_offsets_tenant_isolation ON tenant_event_offsets
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))""")


def downgrade():
    op.drop_table("tenant_event_offsets")
    op.drop_constraint("uq_runtime_events_tenant_sequence", "runtime_events", type_="unique")
    op.drop_column("runtime_events", "sequence")
