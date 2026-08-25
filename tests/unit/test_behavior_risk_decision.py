import pytest
import time
from sentinelayer.behavior.baseline import get_baseline_manager
from sentinelayer.risk.engine import get_risk_engine
from sentinelayer.decision.safety import get_decision_safety

def test_baseline_learning():
    bm = get_baseline_manager()
    
    # Simulate 100 normal requests
    for i in range(100):
        bm.record_request({
            "endpoint": "/api/orders",
            "method": "GET",
            "user_id": "user-123",
            "tenant_id": "tenant-acme",
            "response_time": 0.05 + (i % 10) * 0.01,
            "status_code": 200,
            "request_size": 100,
            "response_size": 500
        })
    
    stats = bm.get_stats()
    assert stats["total_profiles"] == 1
    assert stats["stable_profiles"] == 1

def test_anomaly_detection():
    bm = get_baseline_manager()
    
    # Record normal requests first
    for i in range(50):
        bm.record_request({
            "endpoint": "/api/orders",
            "method": "GET",
            "user_id": "user-123",
            "tenant_id": "tenant-acme",
            "response_time": 0.05,
            "status_code": 200,
            "request_size": 100,
            "response_size": 500
        })
    
    # Anomalous request
    result = bm.detect_anomaly({
        "endpoint": "/api/orders",
        "method": "GET",
        "user_id": "user-123",
        "tenant_id": "tenant-acme",
        "response_time": 0.5,  # 10x normal
        "status_code": 500,
        "request_size": 5000,
        "response_size": 5000
    })
    
    assert "is_anomaly" in result
    assert "score" in result

def test_risk_engine():
    re = get_risk_engine()
    re.clear_signals()
    
    re.add_signal("waf_block", 0.9, source="waf", details={"rule": "SQLI-001"})
    re.add_signal("anomaly_detection", 0.7, source="behavior")
    
    result = re.calculate_risk()
    
    assert result["score"] > 0
    assert result["decision"] in ["allow", "monitor", "challenge", "block"]
    assert len(result["signals"]) == 2

def test_decision_safety():
    ds = get_decision_safety()
    
    # Simulate risk result
    risk_result = {
        "score": 0.8,
        "level": "high",
        "decision": "block",
        "confidence": 0.9,
        "signals": [
            {"name": "waf_block", "score": 0.9, "weight": 1.0}
        ]
    }
    
    decision = ds.make_decision("req-123", risk_result, {"ip": "192.168.1.1"})
    
    assert decision.action == "block"
    assert decision.risk_level == "high"
    assert decision.risk_score == 0.8

def test_kill_switch():
    ds = get_decision_safety()
    
    # Activate kill switch
    ds.activate_kill_switch("Testing")
    assert ds.kill_switch_active is True
    
    # Decision should be block
    risk_result = {"score": 0.1, "level": "low", "decision": "allow", "confidence": 0.5, "signals": []}
    decision = ds.make_decision("req-456", risk_result)
    assert decision.action == "block"
    
    # Deactivate
    ds.deactivate_kill_switch()
    assert ds.kill_switch_active is False

def test_control_plane():
    from sentinelayer.controlplane.models import get_control_plane
    cp = get_control_plane()
    
    # Create tenant
    tenant = cp.create_tenant("Acme Corp", "Test tenant")
    assert tenant.id is not None
    assert tenant.name == "Acme Corp"
    
    # Create application
    app = cp.create_application(tenant.id, "Payment API", "Payment processing", ["/api/payment"])
    assert app is not None
    assert app.tenant_id == tenant.id
    
    # Create policy
    policy = cp.create_policy(tenant.id, "WAF Policy", "waf", [{"rule": "SQLI-001", "action": "block"}])
    assert policy is not None
    assert policy.type == "waf"
    
    # List
    apps = cp.list_applications(tenant.id)
    assert len(apps) == 1
    
    policies = cp.list_policies(tenant.id)
    assert len(policies) == 1
    
    # Stats
    stats = cp.get_stats()
    assert stats["tenants"] >= 1
    assert stats["applications"] >= 1
    assert stats["policies"] >= 1
