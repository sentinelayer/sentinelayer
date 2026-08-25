import pytest
from sentinelayer.backend.internal.auth.authorization import AuthorizationMiddleware, Resource

@pytest.fixture
def auth_middleware():
    return AuthorizationMiddleware()

def test_tenant_isolation_block(auth_middleware):
    resource = Resource("order", "order-123", "tenant-b", "user-b")
    allowed, reason = auth_middleware.validate_request(resource, "tenant-a", "user-a")
    assert allowed is False
    assert "Tenant mismatch" in reason

def test_tenant_isolation_allow(auth_middleware):
    resource = Resource("order", "order-123", "tenant-a", "user-a")
    allowed, reason = auth_middleware.validate_request(resource, "tenant-a", "user-a")
    assert allowed is True

def test_owner_isolation_block(auth_middleware):
    resource = Resource("order", "order-123", "tenant-a", "user-a")
    allowed, reason = auth_middleware.validate_request(resource, "tenant-a", "user-b")
    assert allowed is False
    assert "Resource belongs to another user" in reason

def test_owner_isolation_allow(auth_middleware):
    resource = Resource("order", "order-123", "tenant-a", "user-a")
    allowed, reason = auth_middleware.validate_request(resource, "tenant-a", "user-a")
    assert allowed is True

def test_admin_override(auth_middleware):
    resource = Resource("order", "order-123", "tenant-b", "user-b")
    allowed, reason = auth_middleware.validate_request(resource, "tenant-a", "admin", ["admin"])
    assert allowed is False
    assert "Tenant mismatch" in reason

def test_path_extraction(auth_middleware):
    result = auth_middleware.extract_resource_from_path("/api/v1/orders/order-123")
    assert result is not None
    assert result[0] == "order"
    assert result[1] == "order-123"

def test_validate_request_block(auth_middleware):
    resource = Resource("order", "order-123", "tenant-b", "user-b")
    allowed, reason = auth_middleware.validate_request(resource, "tenant-a", "user-a")
    assert allowed is False
    assert "Tenant mismatch" in reason

def test_bola_protection_with_db_check(auth_middleware):
    resource = Resource("order", "order-123", "tenant-b", "user-b")
    allowed, reason = auth_middleware.validate_request(resource, "tenant-a", "user-a")
    assert allowed is False
    assert "Tenant mismatch" in reason
