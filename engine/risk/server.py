from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from engine.risk.engine import RiskEngine
from engine.risk.decision_matrix import DecisionMatrix
from engine.risk.correlation import RiskCorrelation

app = FastAPI(title="SentinelLayer Risk Engine", version="1.0.0")
engine = RiskEngine()
matrix = DecisionMatrix()
correlation = RiskCorrelation()


class RiskRequest(BaseModel):
    tenant_id: str = ""
    application_id: str = ""
    endpoint: str = ""
    user_id: str = ""
    signals: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    failed_attempts: int = 0
    suspicious_ip: bool = False
    unusual_time: bool = False
    multiple_tenants: bool = False


class RiskResponse(BaseModel):
    action: str
    score: float
    confidence: float
    signals: list[str]
    factors: dict[str, Any]
    explanation: str = ""
    engine_version: str = "1.0.0"


@app.get("/health")
def health():
    return {"status": "healthy", "service": "risk-engine", "version": "1.0.0"}


@app.post("/v1/score", response_model=RiskResponse)
def score(req: RiskRequest):
    ctx = {
        "failed_attempts": req.failed_attempts or int(req.context.get("failed_attempts", 0) or 0),
        "suspicious_ip": req.suspicious_ip or bool(req.context.get("suspicious_ip", False)),
        "unusual_time": req.unusual_time or bool(req.context.get("unusual_time", False)),
        "multiple_tenants": req.multiple_tenants or bool(req.context.get("multiple_tenants", False)),
    }
    base = engine.calculate(ctx)
    score_val = float(base["score"])
    confidence = float(base["confidence"])
    for _ in req.signals:
        score_val = min(100.0, score_val + 12)
        confidence = min(1.0, confidence + 0.05)
    if req.tenant_id:
        for s in req.signals:
            correlation.add_signal(req.tenant_id, s, {"endpoint": req.endpoint})
        corr = correlation.correlate(req.tenant_id)
        score_val = min(100.0, score_val * float(corr.get("risk_multiplier", 1.0)))
    action = matrix.get_action(score_val, confidence)
    if action == "ALLOW" and score_val >= 80:
        action = engine.get_action(score_val)
    return RiskResponse(
        action=action,
        score=round(score_val, 1),
        confidence=round(confidence, 2),
        signals=list(req.signals),
        factors=base.get("factors", {}),
        explanation=f"score={score_val} confidence={confidence}",
        engine_version="1.0.0",
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("RISK_ENGINE_PORT", "8090"))
    uvicorn.run("engine.risk.server:app", host="0.0.0.0", port=port, reload=False)
