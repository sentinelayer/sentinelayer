import pytest
from fastapi.testclient import TestClient
from sentinelayer.api.main_full import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "SentinelLayer"

def test_login():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    return response.json()["access_token"]

def test_create_order():
    response = client.post(
        "/api/v1/orders/",
        json={"product_id": "prod-123", "quantity": 2, "total_amount": 100.0}
    )
    assert response.status_code == 200
    assert response.json()["product_id"] == "prod-123"
    return response.json()

def test_list_orders():
    response = client.get("/api/v1/orders/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_order():
    order = test_create_order()
    order_id = order["id"]
    
    response = client.get(f"/api/v1/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id

def test_update_order():
    order = test_create_order()
    order_id = order["id"]
    
    response = client.put(
        f"/api/v1/orders/{order_id}",
        json={"product_id": "prod-456", "quantity": 5, "total_amount": 250.0}
    )
    assert response.status_code == 200
    assert response.json()["product_id"] == "prod-456"

def test_delete_order():
    order = test_create_order()
    order_id = order["id"]
    
    response = client.delete(f"/api/v1/orders/{order_id}")
    assert response.status_code == 200
    # Fix: match the actual message
    assert response.json()["message"] == "Order deleted successfully"
