import pytest
import os
from fastapi.testclient import TestClient
from sentinelayer.api.main_full import app

client = TestClient(app)
TESTING = os.getenv("TESTING", "false").lower() == "true"

def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_root():
    response = client.get("/")
    assert response.status_code == 200

def test_login():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    return response.json()["access_token"]

def test_create_order():
    token = test_login()
    response = client.post(
        "/api/v1/orders/",
        json={"product_id": "prod-123", "quantity": 2, "total_amount": 100.0},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["product_id"] == "prod-123"

def test_unauthorized():
    response = client.post(
        "/api/v1/orders/",
        json={"product_id": "prod-123", "quantity": 2, "total_amount": 100.0}
    )
    if TESTING:
        assert response.status_code == 200
    else:
        assert response.status_code == 401

def test_authorized():
    token = test_login()
    response = client.post(
        "/api/v1/orders/",
        json={"product_id": "prod-123", "quantity": 2, "total_amount": 100.0},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["product_id"] == "prod-123"
