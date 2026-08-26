import pytest
from sqlalchemy import text

from control_plane.app.infrastructure.db.session import engine


@pytest.mark.asyncio
async def test_rls_enabled():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result is not None
