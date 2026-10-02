import pytest
from httpx import ASGITransport, AsyncClient

from control_plane.app.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200

@pytest.mark.asyncio
async def test_root_serves_dashboard():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")
        assert "SentinelLayer" in resp.text


@pytest.mark.asyncio
async def test_dashboard_spa_fallback():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/events")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")
        assert "<div id=\"root\"></div>" in resp.text
