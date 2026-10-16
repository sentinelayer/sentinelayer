"""The off-path explanation API must not imply an independent AI verdict."""

import asyncio

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from control_plane.app.api.v1.ai_assist import ExplainRequest, explain_decision


@pytest.mark.parametrize("invalid", [-1, 101, float("nan"), float("inf")])
def test_risk_explanation_rejects_invalid_scores(invalid):
    with pytest.raises(ValidationError):
        ExplainRequest(decision="BLOCK", score=invalid)


def test_risk_explanation_uses_separate_mutable_defaults():
    a = ExplainRequest(decision="MONITOR", score=50)
    b = ExplainRequest(decision="ALLOW", score=10)
    a.signals.append("signal-A")
    a.context["source"] = "request-A"
    assert b.signals == []
    assert b.context == {}


def test_risk_explanation_requires_tenant_and_discloses_provenance():
    req = ExplainRequest(decision="BLOCK", score=85, signals=["rate-limit"])
    with pytest.raises(HTTPException) as error:
        asyncio.run(explain_decision(req, x_tenant_id=None))
    assert error.value.status_code == 400
    response = asyncio.run(explain_decision(req, x_tenant_id="tenant-A"))
    assert response["advisory_only"] is True
    assert response["input_origin"] == "caller-supplied"
    assert response["mode"] == "off-path-local"
    assert "rate-limit" in response["explanation"]
