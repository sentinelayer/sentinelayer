import pytest
from sqlalchemy import text
from src.sentinelayer.database import engine
from src.sentinelayer.database.rls import enable_rls

@pytest.mark.asyncio
async def test_rls_enabled():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT relrowsecurity FROM pg_class WHERE relname = 'users'"))
        row = result.first()
        if row:
            assert row[0] is True
        else:
            assert True

@pytest.mark.asyncio
async def test_rls_policy_exists():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT policyname FROM pg_policies WHERE tablename = 'users'"))
        policies = [r[0] for r in result]
        assert "tenant_isolation_policy" in policies
