import pytest
from control_plane.database import engine
from sqlalchemy import text


@pytest.mark.skip(reason="Requires database running")
def test_rls_enabled():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT relrowsecurity FROM pg_class WHERE relname = 'users'"))
        assert result.first()[0] is True
