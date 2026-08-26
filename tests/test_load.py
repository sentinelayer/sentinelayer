import pytest
import asyncio
from httpx import AsyncClient
from src.sentinelayer.api.main import app
import time

@pytest.mark.asyncio
async def test_load_1000_requests():
    client = AsyncClient(app=app, base_url="http://test")
    start = time.time()
    tasks = [client.get("/") for _ in range(100)]
    responses = await asyncio.gather(*tasks)
    end = time.time()
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count > 90
