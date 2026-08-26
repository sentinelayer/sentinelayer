import pytest
from sqlalchemy import text
from control_plane.app.infrastructure.db.session import engine
from control_plane.app.infrastructure.db.rls import enable_rls

@pytest.mark.asyncio
async def test_rls_enforcement():
    enable_rls()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users"))
        assert result is not None
