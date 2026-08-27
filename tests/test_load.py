import asyncio
import time

import pytest
from httpx import ASGITransport, AsyncClient

from control_plane.app.main import app


@pytest.mark.asyncio
async def test_load_1000_requests():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start = time.perf_counter()
        tasks = [client.get("/") for _ in range(1000)]
        responses = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count == 1000
    assert elapsed < 30
