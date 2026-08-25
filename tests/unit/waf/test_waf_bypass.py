import pytest
from sentinelayer.gateway.waf.coraza_wrapper import get_waf_engine

@pytest.fixture
def waf():
    return get_waf_engine()

def test_sql_injection_basic(waf):
    result = waf.inspect_request(
        path="/api/orders",
        query="search=SELECT * FROM users",
        body="",
        headers={}
    )
    assert result["blocked"] is True

def test_sql_injection_encoded(waf):
    result = waf.inspect_request(
        path="/api/orders",
        query="search=SELECT%20%2A%20FROM%20users",
        body="",
        headers={}
    )
    assert result["blocked"] is True

def test_sql_injection_case_mixed(waf):
    result = waf.inspect_request(
        path="/api/orders",
        query="search=SeLeCt * FrOm users",
        body="",
        headers={}
    )
    assert result["blocked"] is True

def test_xss_basic(waf):
    result = waf.inspect_request(
        path="/api/orders",
        query="q=<script>alert(1)</script>",
        body="",
        headers={}
    )
    assert result["blocked"] is True

def test_xss_encoded(waf):
    result = waf.inspect_request(
        path="/api/orders",
        query="q=%3Cscript%3Ealert%281%29%3C/script%3E",
        body="",
        headers={}
    )
    assert result["blocked"] is True

def test_path_traversal_basic(waf):
    result = waf.inspect_request(
        path="/api/orders/../../../etc/passwd",
        query="",
        body="",
        headers={}
    )
    assert result["blocked"] is True

def test_path_traversal_encoded(waf):
    result = waf.inspect_request(
        path="/api/orders/..%2F..%2F..%2Fetc%2Fpasswd",
        query="",
        body="",
        headers={}
    )
    assert result["blocked"] is True

def test_normal_request(waf):
    result = waf.inspect_request(
        path="/api/orders",
        query="status=pending",
        body='{"product_id":"prod-123","quantity":2}',
        headers={"Content-Type": "application/json"}
    )
    assert result["blocked"] is False
    assert len(result["violations"]) == 0
