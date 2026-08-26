import pytest
from httpx import AsyncClient
from control_plane.app.main import app

@pytest.mark.asyncio
async def test_health():
    client = AsyncClient(app=app, base_url="http://test")
    resp = await client.get("/health")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_root():
    client = AsyncClient(app=app, base_url="http://test")
    resp = await client.get("/")
    assert resp.status_code == 200
