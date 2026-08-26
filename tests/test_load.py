import asyncio
import time

import pytest
from httpx import AsyncClient

from control_plane.app.main import app


@pytest.mark.asyncio
async def test_load_1000_requests():
    client = AsyncClient(app=app, base_url="http://test")
    start = time.time()
    tasks = [client.get("/") for _ in range(100)]
    responses = await asyncio.gather(*tasks)
    end = time.time()
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count > 90
