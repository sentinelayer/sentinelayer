import pytest
from sentinelayer.gateway.waf.coraza_wrapper import get_waf_engine

@pytest.fixture
def waf():
    return get_waf_engine()

def test_waf_sql_injection(waf):
    result = waf.inspect_request(
        path="/api/orders",
        query="search=SELECT * FROM users",
        body="",
        headers={}
    )
    # Should detect SQL injection
    assert result["blocked"] is True
    sql_rules = [v for v in result["violations"] if "SQLI" in v["rule_id"]]
    assert len(sql_rules) > 0

def test_waf_xss(waf):
    result = waf.inspect_request(
        path="/api/orders",
        query="q=<script>alert(1)</script>",
        body="",
        headers={}
    )
    assert result["blocked"] is True
    xss_rules = [v for v in result["violations"] if "XSS" in v["rule_id"]]
    assert len(xss_rules) > 0

def test_waf_path_traversal(waf):
    result = waf.inspect_request(
        path="/api/orders/../../../etc/passwd",
        query="",
        body="",
        headers={}
    )
    assert result["blocked"] is True
    path_rules = [v for v in result["violations"] if "PATH" in v["rule_id"]]
    assert len(path_rules) > 0

def test_waf_normal_request(waf):
    result = waf.inspect_request(
        path="/api/orders",
        query="status=pending",
        body='{"product_id":"prod-123","quantity":2}',
        headers={"Content-Type": "application/json"}
    )
    assert result["blocked"] is False
    assert len(result["violations"]) == 0

def test_waf_admin_path(waf):
    result = waf.inspect_request(
        path="/api/orders/admin",
        query="",
        body="",
        headers={}
    )
    assert result["blocked"] is True
    admin_rules = [v for v in result["violations"] if "ADMIN" in v["rule_id"]]
    assert len(admin_rules) > 0

def test_waf_command_injection(waf):
    result = waf.inspect_request(
        path="/api/orders",
        query="cmd=; ls -la",
        body="",
        headers={}
    )
    assert result["blocked"] is True
    cmd_rules = [v for v in result["violations"] if "CMD" in v["rule_id"]]
    assert len(cmd_rules) > 0

def test_waf_ssrf(waf):
    result = waf.inspect_request(
        path="/api/orders",
        query="url=http://169.254.169.254/latest/meta-data",
        body="",
        headers={}
    )
    assert result["blocked"] is True
    ssrf_rules = [v for v in result["violations"] if "SSRF" in v["rule_id"]]
    assert len(ssrf_rules) > 0
