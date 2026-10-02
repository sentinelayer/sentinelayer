import pytest
from control_plane.gateway.ratelimit.sliding_window import SimpleRateLimiter


@pytest.fixture
def limiter():
    return SimpleRateLimiter()

def test_rate_limit(limiter):
    identifier = "test-user-123"

    # 100 requests allowed
    for i in range(100):
        result = limiter.is_allowed("user", identifier, "/api/test", limit=100)
        assert result["allowed"] is True

    # 101st blocked
    result = limiter.is_allowed("user", identifier, "/api/test", limit=100)
    assert result["allowed"] is False

def test_different_dimensions(limiter):
    # User A: 10 requests
    for i in range(10):
        result = limiter.is_allowed("user", "user-a", "/api/test", limit=10)
        assert result["allowed"] is True

    # User B: still allowed (different dimension)
    result = limiter.is_allowed("user", "user-b", "/api/test", limit=10)
    assert result["allowed"] is True

def test_endpoint_isolation(limiter):
    identifier = "user-123"

    # Endpoint A: 5 requests
    for i in range(5):
        result = limiter.is_allowed("user", identifier, "/api/a", limit=5)
        assert result["allowed"] is True

    # Endpoint B: still allowed (different endpoint)
    result = limiter.is_allowed("user", identifier, "/api/b", limit=5)
    assert result["allowed"] is True

def test_window_reset(limiter, monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr("control_plane.gateway.ratelimit.sliding_window.time.monotonic", lambda: clock[0])
    identifier = "test-user"

    # 10 requests
    for i in range(10):
        result = limiter.is_allowed("user", identifier, "/api/test", limit=10)
        assert result["allowed"] is True

    # 11th blocked
    result = limiter.is_allowed("user", identifier, "/api/test", limit=10)
    assert result["allowed"] is False
    assert result["reset_in"] > 0

    # Advance only the limiter clock; no wall-clock delay.
    clock[0] += 61

    # Should be allowed again
    result = limiter.is_allowed("user", identifier, "/api/test", limit=10)
    assert result["allowed"] is True
