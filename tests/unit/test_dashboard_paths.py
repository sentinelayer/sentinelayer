import pytest
from fastapi.testclient import TestClient

from control_plane.app import main


@pytest.fixture
def dashboard(tmp_path, monkeypatch):
    root = tmp_path / "dashboard"
    root.mkdir()
    index = root / "index.html"
    index.write_text("<div>dashboard-safe</div>")
    secret = tmp_path / "secret.txt"
    secret.write_text("outside-dashboard-secret")
    monkeypatch.setattr(main, "DASHBOARD_DIST", root.resolve())
    monkeypatch.setattr(main, "DASHBOARD_INDEX", index)
    return root, secret


@pytest.mark.asyncio
async def test_dashboard_fallback_cannot_read_parent_directory(dashboard):
    response = await main.dashboard_fallback("../secret.txt")
    assert response.path.name == "index.html"


@pytest.mark.asyncio
async def test_dashboard_fallback_cannot_follow_outside_symlink(dashboard):
    root, secret = dashboard
    (root / "linked.txt").symlink_to(secret)
    response = await main.dashboard_fallback("linked.txt")
    assert response.path.name == "index.html"


def test_encoded_traversal_does_not_expose_outside_content(dashboard):
    response = TestClient(main.app).get("/%2e%2e/secret.txt")
    assert "outside-dashboard-secret" not in response.text
    assert response.status_code == 200
