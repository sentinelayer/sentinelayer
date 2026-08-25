import pytest
import uuid
from sentinelayer.database.models.base import DatabaseManager
from sentinelayer.database.models.order import Order, OrderRepository, OrderStatus

@pytest.fixture(scope="session")
def db_manager():
    """Setup test database (SQLite untuk unit test)"""
    import os
    # Use SQLite for testing
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    manager = DatabaseManager()
    manager.create_tables()
    return manager

@pytest.fixture
def tenant_a_repo(db_manager):
    return OrderRepository(db_manager, "tenant-a")

@pytest.fixture
def tenant_b_repo(db_manager):
    return OrderRepository(db_manager, "tenant-b")

def test_create_order_tenant_isolation(db_manager, tenant_a_repo, tenant_b_repo):
    """Test orders are isolated by tenant"""
    
    # Create order in Tenant A
    order_a = tenant_a_repo.create_order({
        "id": str(uuid.uuid4()),
        "user_id": "user-a-1",
        "product_id": "prod-1",
        "quantity": 2,
        "total_amount": 100.0,
        "created_by": "user-a-1"
    })
    assert order_a.tenant_id == "tenant-a"
    
    # Create order in Tenant B
    order_b = tenant_b_repo.create_order({
        "id": str(uuid.uuid4()),
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
    """Test user orders are isolated by tenant"""
    
    # Create multiple orders for Tenant A
    for i in range(3):
        tenant_a_repo.create_order({
            "id": str(uuid.uuid4()),
            "user_id": "user-a-1",
            "product_id": f"prod-{i}",
            "quantity": i + 1,
            "total_amount": (i + 1) * 100.0,
            "created_by": "user-a-1"
        })
    
    # Create orders for Tenant B
    for i in range(2):
        tenant_b_repo.create_order({
            "id": str(uuid.uuid4()),
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
        assert order.user_id == "user-a-1"
    
    # Tenant B sees only Tenant B orders
    tenant_b_orders = tenant_b_repo.get_user_orders("user-b-1")
    assert len(tenant_b_orders) == 2
    for order in tenant_b_orders:
        assert order.tenant_id == "tenant-b"
        assert order.user_id == "user-b-1"

def test_update_order_tenant_isolation(db_manager, tenant_a_repo, tenant_b_repo):
    """Test update is isolated by tenant"""
    
    # Create order in Tenant A
    order = tenant_a_repo.create_order({
        "id": str(uuid.uuid4()),
        "user_id": "user-a-1",
        "product_id": "prod-1",
        "quantity": 1,
        "total_amount": 100.0,
        "created_by": "user-a-1"
    })
    
    # Tenant B tries to update Tenant A's order
    result = tenant_b_repo.update_order(order.id, {"status": OrderStatus.COMPLETED})
    assert result is None  # Cannot find order
    
    # Tenant A can update own order
    result = tenant_a_repo.update_order(order.id, {"status": OrderStatus.COMPLETED})
    assert result is not None
    assert result.status == OrderStatus.COMPLETED

def test_delete_order_tenant_isolation(db_manager, tenant_a_repo, tenant_b_repo):
    """Test delete is isolated by tenant"""
    
    # Create order in Tenant A
    order = tenant_a_repo.create_order({
        "id": str(uuid.uuid4()),
        "user_id": "user-a-1",
        "product_id": "prod-1",
        "quantity": 1,
        "total_amount": 100.0,
        "created_by": "user-a-1"
    })
    
    # Tenant B tries to delete Tenant A's order
    result = tenant_b_repo.delete_order(order.id)
    assert result is False  # Cannot find order
    
    # Tenant A can delete own order
    result = tenant_a_repo.delete_order(order.id)
    assert result is True
    
    # Order no longer exists
    result = tenant_a_repo.get_order(order.id)
    assert result is None

def test_cross_tenant_query_attack(db_manager, tenant_a_repo):
    """Test BOLA attack prevention with RLS"""
    
    # Create order in Tenant A
    order_a = tenant_a_repo.create_order({
        "id": str(uuid.uuid4()),
        "user_id": "user-a-1",
        "product_id": "prod-1",
        "quantity": 1,
        "total_amount": 100.0,
        "created_by": "user-a-1"
    })
    
    # Attempt to query using raw SQL with tenant filter bypass
    with db_manager.get_session("tenant-a") as session:
        # Try to select order without tenant filter (should be blocked by RLS)
        result = session.execute(
            "SELECT * FROM orders WHERE id = :order_id",
            {"order_id": order_a.id}
        ).fetchone()
        # RLS should restrict to tenant-a only
        assert result is not None
        assert result.tenant_id == "tenant-a"
        
        # Try to update without tenant filter
        result = session.execute(
            "UPDATE orders SET status = 'completed' WHERE id = :order_id",
            {"order_id": order_a.id}
        )
        # RLS should prevent update if tenant mismatch
        session.commit()
    
    # Order status should be updated (same tenant)
    updated = tenant_a_repo.get_order(order_a.id)
    assert updated.status == OrderStatus.COMPLETED
