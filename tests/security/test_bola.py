import pytest
from httpx import AsyncClient
from src.sentinelayer.api.main_full import app

@pytest.mark.asyncio
async def test_bola_prevention():
    client = AsyncClient(app=app, base_url="http://test")

    resp = await client.post("/api/v1/auth/login", json={
        "email": "userA@test.com",
        "password": "password123"
    })
    token_a = resp.json()["access_token"]

    resp = await client.post("/api/v1/auth/login", json={
        "email": "userB@test.com",
        "password": "password123"
    })
    token_b = resp.json()["access_token"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    resp = await client.post("/api/v1/orders/", json={"name": "Order A"}, headers=headers_a)
    order_id = resp.json()["id"]

    headers_b = {"Authorization": f"Bearer {token_b}"}
    resp = await client.get(f"/api/v1/orders/{order_id}", headers=headers_b)
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_idor_prevention():
    client = AsyncClient(app=app, base_url="http://test")

    resp = await client.post("/api/v1/auth/register", json={
        "email": "userA2@test.com",
        "password": "password123",
        "full_name": "User A",
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
    })
    assert resp.status_code == 201

    resp = await client.post("/api/v1/auth/login", json={
        "email": "userA2@test.com",
        "password": "password123"
    })
    token_a = resp.json()["access_token"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    resp = await client.get("/api/v1/admin/users", headers=headers_a)
    assert resp.status_code == 403
