"""Request-bound risk decisions must reject malformed security signals."""

import pytest
from pydantic import ValidationError

from engine.risk.server import RiskRequest


@pytest.mark.parametrize("payload", [
    {"failed_attempts": -1},
    {"failed_attempts": True},
    {"failed_attempts": "100"},
    {"failed_attempts": 10_001},
    {"context": {"failed_attempts": "999999999999999999999999999999999"}},
    {"context": {"failed_attempts": -1}},
    {"context": {"failed_attempts": False}},
    {"context": {"suspicious_ip": "false"}},
    {"context": {"unusual_time": 1}},
    {"context": {"multiple_tenants": "true"}},
    {"context": {"criticality": ["critical"]}},
    {"signals": ["auth_failure"] * 129},
    {"unexpected_flag": "bypass"},
])
def test_invalid_risk_input_never_reaches_decision(payload):
    with pytest.raises(ValidationError):
        RiskRequest.model_validate(payload)


def test_valid_gateway_risk_payload_remains_compatible():
    model = RiskRequest.model_validate({
        "tenant_id": "tenant-a",
        "endpoint": "/api/v1/checkout",
        "signals": ["auth_failure", "rate_limit_exceeded"],
        "failed_attempts": 9,
        "context": {
            "failed_attempts": 9,
            "suspicious_ip": False,
            "unusual_time": True,
            "multiple_tenants": False,
            "criticality": "critical",
        },
    })
    assert model.failed_attempts == 9
    assert model.context["criticality"] == "critical"
