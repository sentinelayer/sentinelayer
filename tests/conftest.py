import pytest
from fastapi.testclient import TestClient
from src.sentinelayer.api.main import app

@pytest.fixture
def client():
    return TestClient(app)
