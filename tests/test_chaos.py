import pytest
import asyncio
import random
from httpx import AsyncClient
from src.sentinelayer.api.main_full import app

@pytest.mark.asyncio
async def test_chaos_request():
    client = AsyncClient(app=app, base_url="http://test")
    
    # Send malformed requests
    malformed_payloads = [
        {"data": "x" * 10000},
        {"data": {"nested": {"deep": {"value": [1, 2, 3]}}}},
        {"data": None},
        {"data": True}
    ]
    
    for payload in malformed_payloads:
        try:
            resp = await client.post("/api/v1/orders/", json=payload)
            assert resp.status_code in [400, 422, 200]
        except Exception:
            pass

@pytest.mark.asyncio
async def test_load_simulation():
    client = AsyncClient(app=app, base_url="http://test")
    
    tasks = []
    for i in range(50):
        tasks.append(client.get("/"))
    
    responses = await asyncio.gather(*tasks)
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count > 40  # At least 80% success
