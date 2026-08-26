from engine.behavior import BehaviorEngine
from engine.behavior.baseline.lifecycle import BaselineLifecycle


def test_frequency_anomaly_elevated():
    eng = BehaviorEngine(window_minutes=5)
    for _ in range(25):
        eng.track({"user_id": "u1", "endpoint": "/api/x", "tenant_id": "t1"})
    r = eng.detect_frequency_anomaly("u1")
    assert r["is_anomaly"] is True
    assert "freq_elevated" in r["signals"] or "freq_critical" in r["signals"]


def test_sequence_fraud_pattern():
    eng = BehaviorEngine()
    for step in ["login", "add_payment", "coupon", "refund"]:
        eng.track({"user_id": "u2", "tenant_id": "t1", "endpoint": step})
    r = eng.detect_sequence_abuse("t1", "u2")
    assert r["is_anomaly"] is True
    assert "sequence_fraud" in r["signals"]


def test_analyze_returns_signals():
    eng = BehaviorEngine()
    for _ in range(30):
        eng.track({"user_id": "u3", "tenant_id": "t1", "endpoint": "/api/y"})
    out = eng.analyze({"user_id": "u3", "tenant_id": "t1", "endpoint": "/api/y"})
    assert "signals" in out
    assert out["is_anomaly"] is True


def test_baseline_lifecycle():
    lc = BaselineLifecycle(min_samples=5)
    for v in [10.0, 11.0, 9.5, 10.5, 10.2, 9.8]:
        lc.collect("/api/orders", v)
    assert lc.validate("/api/orders") is True
    b = lc.establish("/api/orders")
    assert b is not None
    assert "mean" in b
    mon = lc.monitor("/api/orders", 50.0)
    assert mon["anomaly"] is True
    mon2 = lc.monitor("/api/orders", 10.1)
    assert mon2["anomaly"] is False
    lc.rollback("/api/orders")
    assert "/api/orders" not in lc.baseline
