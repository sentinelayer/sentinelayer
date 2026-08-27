import asyncio

import httpx
import pytest

from control_plane.app.main import app


@pytest.mark.asyncio
async def test_chaos_health_probe_has_explicit_failure_signal():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"


@pytest.mark.asyncio
async def test_chaos_concurrent_requests_are_observed_without_swallowing_errors():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        responses = await asyncio.gather(*(client.get("/") for _ in range(10)))

    assert len(responses) == 10
    assert all(response.status_code == 200 for response in responses)
