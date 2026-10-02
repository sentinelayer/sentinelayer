"""Verify migrated tenant tables have RLS and tenant-scoped read/write policies."""
import os

import pytest
from sqlalchemy import text

from control_plane.app.infrastructure.db.models import Base
from control_plane.app.infrastructure.db.session import engine


@pytest.mark.integration
def test_migrated_tenant_tables_have_rls_policies():
    if engine.dialect.name != "postgresql" or os.getenv("TEST_POSTGRES_RLS") != "1":
        pytest.skip("requires disposable PostgreSQL with TEST_POSTGRES_RLS=1")
    tenant_tables = {table.name for table in Base.metadata.tables.values() if "tenant_id" in table.c}
    tenant_tables.add("tenants")
    assert tenant_tables
    with engine.connect() as connection:
        for name in sorted(tenant_tables):
            enabled = connection.scalar(text(
                "SELECT relrowsecurity FROM pg_class WHERE oid = to_regclass(:name)"
            ), {"name": name})
            assert enabled is True, f"RLS missing for {name}"
            policies = connection.execute(text(
                "SELECT qual, with_check, roles FROM pg_policies WHERE schemaname = 'public' AND tablename = :name"
            ), {"name": name}).all()
            assert policies, f"Tenant policy missing for {name}"
            assert any("app.tenant_id" in (read or "") for read, write, roles in policies)
            for read, write, roles in policies:
                if set(roles).issubset({"sentinel_auth", "sentinel_worker"}):
                    continue
                assert "app.tenant_id" in (read or ""), f"Read policy unscoped for {name}"
                assert "app.tenant_id" in (write or ""), f"Write policy unscoped for {name}"
