import pytest
import uuid
from sentinelayer.database.models.base import DatabaseManager

@pytest.fixture(scope="function")
def db_manager():
    """Setup test database (SQLite for unit tests)"""
    import os
    os.environ["DATABASE_URL"] = "sqlite:///./test_rls.db"
    manager = DatabaseManager()
    # Drop existing tables
    manager.create_tables()
    return manager

@pytest.fixture
def tenant_a_repo(db_manager):

@pytest.fixture
def tenant_b_repo(db_manager):

def test_create_order_tenant_isolation(db_manager, tenant_a_repo, tenant_b_repo):
    # Create order in Tenant A
    order_a = tenant_a_repo.create_order({
        "user_id": "user-a-1",
        "product_id": "prod-1",
        "quantity": 2,
        "total_amount": 100.0,
        "created_by": "user-a-1"
    })
    assert order_a.tenant_id == "tenant-a"
    
    # Create order in Tenant B
    order_b = tenant_b_repo.create_order({
        "user_id": "user-b-1",
        "product_id": "prod-2",
        "quantity": 1,
        "total_amount": 50.0,
        "created_by": "user-b-1"
    })
    assert order_b.tenant_id == "tenant-b"
    
    # Tenant A cannot see Tenant B's order
    result = tenant_a_repo.get_order(order_b.id)
    assert result is None
    
    # Tenant B cannot see Tenant A's order
    result = tenant_b_repo.get_order(order_a.id)
    assert result is None

def test_get_user_orders_tenant_isolation(db_manager, tenant_a_repo, tenant_b_repo):
    # Create orders for Tenant A
    for i in range(3):
        tenant_a_repo.create_order({
            "user_id": "user-a-1",
            "product_id": f"prod-{i}",
            "quantity": i + 1,
            "total_amount": (i + 1) * 100.0,
            "created_by": "user-a-1"
        })
    
    # Create orders for Tenant B
    for i in range(2):
        tenant_b_repo.create_order({
            "user_id": "user-b-1",
            "product_id": f"prod-{i}",
            "quantity": i + 1,
            "total_amount": (i + 1) * 50.0,
            "created_by": "user-b-1"
        })
    
    # Tenant A sees only Tenant A orders
    tenant_a_orders = tenant_a_repo.get_user_orders("user-a-1")
    assert len(tenant_a_orders) == 3
    for order in tenant_a_orders:
        assert order.tenant_id == "tenant-a"
    
    # Tenant B sees only Tenant B orders
    tenant_b_orders = tenant_b_repo.get_user_orders("user-b-1")
    assert len(tenant_b_orders) == 2
    for order in tenant_b_orders:
        assert order.tenant_id == "tenant-b"

def test_update_order_tenant_isolation(db_manager, tenant_a_repo, tenant_b_repo):
    order = tenant_a_repo.create_order({
        "user_id": "user-a-1",
        "product_id": "prod-1",
        "quantity": 1,
        "total_amount": 100.0,
        "created_by": "user-a-1"
    })
    
    # Tenant B tries to update Tenant A's order
    assert result is None
    
    # Tenant A can update own order
    assert result is not None

def test_delete_order_tenant_isolation(db_manager, tenant_a_repo, tenant_b_repo):
    order = tenant_a_repo.create_order({
        "user_id": "user-a-1",
        "product_id": "prod-1",
        "quantity": 1,
        "total_amount": 100.0,
        "created_by": "user-a-1"
    })
    
    # Tenant B tries to delete Tenant A's order
    result = tenant_b_repo.delete_order(order.id)
    assert result is False
    
    # Tenant A can delete own order
    result = tenant_a_repo.delete_order(order.id)
    assert result is True
    
    result = tenant_a_repo.get_order(order.id)
    assert result is None
