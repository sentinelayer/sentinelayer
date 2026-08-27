import os
import uuid

import pytest
import psycopg2
from control_plane.app.infrastructure.db.session import engine


@pytest.mark.integration
def test_postgres_rls_isolation_with_unprivileged_role():
    if engine.dialect.name != "postgresql":
        pytest.skip("requires PostgreSQL")
    if os.getenv("TEST_POSTGRES_RLS") != "1":
        pytest.skip("set TEST_POSTGRES_RLS=1 to run live PostgreSQL RLS evidence")

    role = f"sl_rls_probe_{uuid.uuid4().hex[:12]}"
    role_password = uuid.uuid4().hex
    tenant_a = f"rls-a-{uuid.uuid4().hex}"
    tenant_b = f"rls-b-{uuid.uuid4().hex}"
    hold_a = str(uuid.uuid4())
    hold_b = str(uuid.uuid4())
    database_url = os.environ["DATABASE_URL"]
    admin = engine.raw_connection()
    try:
        admin.autocommit = True
        with admin.cursor() as cur:
            cur.execute("CREATE ROLE \"%s\" LOGIN PASSWORD %%s" % role, (role_password,))
            cur.execute("GRANT USAGE ON SCHEMA public TO \"%s\"" % role)
            cur.execute("GRANT SELECT, INSERT ON legal_holds TO \"%s\"" % role)
            cur.execute("ALTER TABLE legal_holds FORCE ROW LEVEL SECURITY")
            cur.execute(
                "INSERT INTO tenants (id, name) VALUES (%s, %s), (%s, %s)",
                (tenant_a, "RLS A", tenant_b, "RLS B"),
            )
            cur.execute(
                "INSERT INTO legal_holds (id, tenant_id, reason, scope, status, created_at) VALUES "
                "(%s, %s, %s, %s, %s, now()), (%s, %s, %s, %s, %s, now())",
                (hold_a, tenant_a, "test-a", "{}", "active", hold_b, tenant_b, "test-b", "{}", "active"),
            )

        user = psycopg2.connect(database_url, user=role, password=role_password)
        try:
            with user.cursor() as cur:
                cur.execute("SELECT set_config('app.tenant_id', %s, false)", (tenant_a,))
                cur.execute("SELECT id, tenant_id FROM legal_holds ORDER BY id")
                assert cur.fetchall() == [(hold_a, tenant_a)]
                with pytest.raises(psycopg2.errors.InsufficientPrivilege):
                    cur.execute(
                        "INSERT INTO legal_holds (id, tenant_id, reason, scope, status, created_at) "
                        "VALUES (%s, %s, %s, %s, %s, now())",
                        (str(uuid.uuid4()), tenant_b, "cross-tenant", "{}", "active"),
                    )
                user.rollback()
        finally:
            user.close()
    finally:
        with admin.cursor() as cur:
            cur.execute("ALTER TABLE legal_holds NO FORCE ROW LEVEL SECURITY")
            cur.execute("DELETE FROM legal_holds WHERE id IN (%s, %s)", (hold_a, hold_b))
            cur.execute("DELETE FROM tenants WHERE id IN (%s, %s)", (tenant_a, tenant_b))
            cur.execute("DROP ROLE IF EXISTS \"%s\"" % role)
        admin.close()


def test_rls_probe_is_explicitly_skipped_without_postgres():
    if engine.dialect.name != "postgresql":
        pytest.skip("requires PostgreSQL")
    assert os.getenv("TEST_POSTGRES_RLS") != "1"
