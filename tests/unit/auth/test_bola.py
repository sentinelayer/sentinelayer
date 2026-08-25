import pytest
from sentinelayer.backend.internal.auth.authorization import AuthorizationMiddleware, Resource

@pytest.fixture
def auth_middleware():
    return AuthorizationMiddleware()

def test_tenant_isolation_block(auth_middleware):
    """Tenant A coba akses resource Tenant B -> HARUS GAGAL"""
    resource = Resource(
        type="order",
        id="order-123",
        tenant_id="tenant-b",
        owner_id="user-b"
    )
    allowed, reason = auth_middleware.validate_request(
        resource=resource,
        user_tenant_id="tenant-a",
        user_id="user-a"
    )
    assert allowed is False
    assert "Tenant mismatch" in reason

def test_tenant_isolation_allow(auth_middleware):
    """Tenant A akses resource Tenant A -> HARUS BERHASIL"""
    resource = Resource(
        type="order",
        id="order-123",
        tenant_id="tenant-a",
        owner_id="user-a"
    )
    allowed, reason = auth_middleware.validate_request(
        resource=resource,
        user_tenant_id="tenant-a",
        user_id="user-a"
    )
    assert allowed is True
    assert "Access granted" in reason

def test_owner_isolation_block(auth_middleware):
    """User B coba akses resource User A -> HARUS GAGAL"""
    resource = Resource(
        type="order",
        id="order-123",
        tenant_id="tenant-a",
        owner_id="user-a"
    )
    allowed, reason = auth_middleware.validate_request(
        resource=resource,
        user_tenant_id="tenant-a",
        user_id="user-b"
    )
    assert allowed is False
    assert "Resource belongs to another user" in reason

def test_owner_isolation_allow(auth_middleware):
    """User A akses resource sendiri -> HARUS BERHASIL"""
    resource = Resource(
        type="order",
        id="order-123",
        tenant_id="tenant-a",
        owner_id="user-a"
    )
    allowed, reason = auth_middleware.validate_request(
        resource=resource,
        user_tenant_id="tenant-a",
        user_id="user-a"
    )
    assert allowed is True

def test_admin_override(auth_middleware):
    """Admin bisa akses semua resource"""
    resource = Resource(
        type="order",
        id="order-123",
        tenant_id="tenant-b",
        owner_id="user-b"
    )
    allowed, reason = auth_middleware.validate_request(
        resource=resource,
        user_tenant_id="tenant-a",
        user_id="admin",
        user_roles=["admin"]
    )
    assert allowed is True
    assert "Admin override" in reason

def test_path_extraction(auth_middleware):
    result = auth_middleware.extract_resource_from_path("/api/v1/orders/order-123")
    assert result is not None
    assert result[0] == "order"
    assert result[1] == "order-123"

def test_validate_request_block(auth_middleware):
    resource = Resource(
        type="order",
        id="order-123",
        tenant_id="tenant-b",
        owner_id="user-b"
    )
    allowed, reason = auth_middleware.validate_request(
        resource=resource,
        user_tenant_id="tenant-a",
        user_id="user-a"
    )
    assert allowed is False
    assert "Tenant mismatch" in reason

def test_bola_protection_with_db_check(auth_middleware):
    """Simulasi BOLA check dengan data dari database"""
    db_resource = Resource(
        type="order",
        id="order-123",
        tenant_id="tenant-b",
        owner_id="user-b"
    )
    allowed, reason = auth_middleware.validate_request(
        resource=db_resource,
        user_tenant_id="tenant-a",
        user_id="user-a"
    )
    assert allowed is False
    assert "Tenant mismatch" in reason
