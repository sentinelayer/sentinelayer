from __future__ import annotations

import os
import uuid

import pytest
from httpx import AsyncClient

BASE = os.getenv("CONTROL_PLANE_URL", "http://localhost:8005")
PATHS = [
    "/api/v1/tenants",
    "/api/v1/applications",
    "/api/v1/policies",
    "/api/v1/evidence",
    "/api/v1/incidents",
    "/api/v1/alerts",
    "/api/v1/events",
    "/api/v1/audit",
]


def _uid() -> str:
    return uuid.uuid4().hex[:8]


@pytest.mark.asyncio
async def test_unauthenticated_sensitive_paths_rejected():
    async with AsyncClient(base_url=BASE, timeout=10.0) as client:
        for path in PATHS:
            resp = await client.get(path)
            assert resp.status_code in (401, 403, 404, 422), f"{path} -> {resp.status_code}"


@pytest.mark.asyncio
async def test_tenant_b_cannot_see_tenant_a_resources():
    async with AsyncClient(base_url=BASE, timeout=15.0) as client:
        ta, tb = f"ta-{_uid()}", f"tb-{_uid()}"
        ea, eb = f"{ta}@test.local", f"{tb}@test.local"
        password = "TestPass12chars!"
        await client.post("/api/v1/auth/register", json={"email": ea, "password": password, "full_name": "A", "tenant_id": ta})
        await client.post("/api/v1/auth/register", json={"email": eb, "password": password, "full_name": "B", "tenant_id": tb})
        la = await client.post("/api/v1/auth/login", json={"email": ea, "password": password})
        lb = await client.post("/api/v1/auth/login", json={"email": eb, "password": password})
        if la.status_code != 200 or lb.status_code != 200:
            pytest.skip("login not available")
        token_a = la.json().get("access_token") or la.json().get("token")
        token_b = lb.json().get("access_token") or lb.json().get("token")
        ha = {"Authorization": f"Bearer {token_a}", "X-Tenant-ID": ta}
        hb = {"Authorization": f"Bearer {token_b}", "X-Tenant-ID": tb}
        await client.post("/api/v1/applications", headers=ha, json={"name": f"seed-{_uid()}", "environment": "production"})
        for path in PATHS:
            rb = await client.get(path, headers=hb)
            if rb.status_code != 200:
                continue
            data = rb.json()
            items = data if isinstance(data, list) else data.get("items") or data.get("data") or []
            for item in items:
                tid = str(item.get("tenant_id") or item.get("tenant") or "")
                assert tid in ("", tb), f"leak on {path}: {tid}"
