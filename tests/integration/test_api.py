import pytest
from fastapi.testclient import TestClient
from sentinelayer.api.main import app
import uuid

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_login():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    return response.json()["access_token"]

def test_create_order():
    # Get token
    token = test_login()
    
    # Create order
    response = client.post(
        "/api/v1/orders/",
        json={
            "product_id": "prod-123",
            "quantity": 2,
            "total_amount": 100.0
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["product_id"] == "prod-123"
    assert response.json()["quantity"] == 2
    assert response.json()["total_amount"] == 100.0
    return response.json()

def test_get_order():
    # Create order first
    token = test_login()
    order = test_create_order()
    order_id = order["id"]
    
    # Get order
    response = client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == order_id

def test_list_orders():
    token = test_login()
    
    # Create multiple orders
    for i in range(3):
        client.post(
            "/api/v1/orders/",
            json={
                "product_id": f"prod-{i}",
                "quantity": i + 1,
                "total_amount": (i + 1) * 100.0
            },
            headers={"Authorization": f"Bearer {token}"}
        )
    
    # List orders
    response = client.get(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_unauthorized():
    # Try to access without token
    response = client.get("/api/v1/orders/")
    assert response.status_code == 401
    
    # Try with invalid token
    response = client.get(
        "/api/v1/orders/",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401
