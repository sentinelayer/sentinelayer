from __future__ import annotations

import os
import uuid

import pytest
from httpx import AsyncClient

BASE = os.getenv("CONTROL_PLANE_URL", "http://localhost:8005")


def _uid() -> str:
    return uuid.uuid4().hex[:10]


@pytest.mark.asyncio
async def test_bola_cross_tenant_object_access_denied():
    async with AsyncClient(base_url=BASE, timeout=15.0) as client:
        ta = f"tenant-a-{_uid()}"
        tb = f"tenant-b-{_uid()}"
        ea = f"a-{_uid()}@example.com"
        eb = f"b-{_uid()}@example.com"
        password = "TestPass12chars!"

        ra = await client.post("/api/v1/auth/register", json={"email": ea, "password": password, "full_name": "A", "tenant_id": ta})
        rb = await client.post("/api/v1/auth/register", json={"email": eb, "password": password, "full_name": "B", "tenant_id": tb})
        assert ra.status_code == 200, ra.text
        assert rb.status_code == 200, rb.text

        la = await client.post("/api/v1/auth/login", json={"email": ea, "password": password})
        lb = await client.post("/api/v1/auth/login", json={"email": eb, "password": password})
        assert la.status_code == 200, la.text
        assert lb.status_code == 200, lb.text

        token_a = la.json().get("access_token") or la.json().get("token")
        token_b = lb.json().get("access_token") or lb.json().get("token")
        assert token_a and token_b

        headers_a = {"Authorization": f"Bearer {token_a}", "X-Tenant-ID": ta}
        headers_b = {"Authorization": f"Bearer {token_b}", "X-Tenant-ID": tb}

        create = await client.post("/api/v1/applications", headers=headers_a, json={"name": f"app-a-{_uid()}", "environment": "production"})
        assert create.status_code == 200, create.text

        body = create.json()
        obj_id = body.get("id") or body.get("application_id") or body.get("policy_id")
        assert obj_id

        owner = await client.get(f"/api/v1/applications/{obj_id}", headers=headers_a)
        assert owner.status_code == 200, owner.text
        assert owner.json()["id"] == obj_id

        for path in (f"/api/v1/applications/{obj_id}",):
            resp = await client.get(path, headers=headers_b)
            assert resp.status_code in (403, 404, 401), f"BOLA FAIL: {resp.status_code} on {path}"

        for list_path in ("/api/v1/applications", "/api/v1/policies"):
            resp = await client.get(list_path, headers=headers_b)
            assert resp.status_code == 200, resp.text
            data = resp.json()
            items = data if isinstance(data, list) else data.get("items") or data.get("data") or []
            ids = [str(i.get("id") or i.get("application_id") or i.get("policy_id") or "") for i in items]
            assert str(obj_id) not in ids
