from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from engine.decision.safety_layer import SafetyLayer
from engine.risk.calibration import Calibration
from engine.risk.correlation import CorrelationUnavailable, RiskCorrelation
from engine.risk.decision_matrix import DecisionMatrix
from engine.risk.engine import RiskEngine
from engine.risk.signal_catalog import SignalCatalog

app = FastAPI(title="SentinelLayer Risk Engine", version="1.1.0")
engine = RiskEngine()
matrix = DecisionMatrix()
correlation = RiskCorrelation(
    redis_url=os.getenv("REDIS_URL"),
    require_shared=os.getenv("SL_ENV", "development").lower() in {"production", "prod"},
)
catalog = SignalCatalog()
calibration = Calibration()
safety = SafetyLayer(mode=os.getenv("RISK_SAFETY_MODE", "production"))

try:
    configured_factor = float(os.getenv("RISK_CALIBRATION_FACTOR", "1.0"))
except ValueError:
    configured_factor = 1.0
if configured_factor > 0:
    calibration.set_factor(configured_factor)


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
    engine_version: str = "1.1.0"


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "risk-engine",
        "version": "1.1.0",
        "catalog_signals": len(catalog.list_signals()),
        "calibration_factor": calibration.get_factor(),
        "safety_mode": safety.mode,
    }


@app.post("/v1/score", response_model=RiskResponse)
def score(req: RiskRequest):
    ctx = {
        "failed_attempts": max(0, req.failed_attempts or int(req.context.get("failed_attempts", 0) or 0)),
        "suspicious_ip": req.suspicious_ip or bool(req.context.get("suspicious_ip", False)),
        "unusual_time": req.unusual_time or bool(req.context.get("unusual_time", False)),
        "multiple_tenants": req.multiple_tenants or bool(req.context.get("multiple_tenants", False)),
    }
    base = engine.calculate(ctx)
    raw_score = float(base["score"])
    signal_weights: dict[str, int] = {}
    unknown_signals: list[str] = []
    for signal in dict.fromkeys(req.signals):
        if signal not in catalog.signals:
            unknown_signals.append(signal)
        signal_weights[signal] = catalog.get_weight(signal)
        raw_score = min(100.0, raw_score + signal_weights[signal])

    confidence = float(base["confidence"])
    if req.signals:
        confidence = min(1.0, confidence + min(0.2, 0.03 * len(signal_weights)))
    if unknown_signals:
        confidence = max(0.0, confidence - 0.1)

    correlation_data: dict[str, Any] = {"risk_multiplier": 1.0, "signal_count": 0}
    if req.tenant_id:
        try:
            for signal in dict.fromkeys(req.signals):
                correlation.add_signal(req.tenant_id, signal, {"endpoint": req.endpoint})
            correlation_data = correlation.correlate(req.tenant_id)
            raw_score = min(100.0, raw_score * float(correlation_data["risk_multiplier"]))
        except CorrelationUnavailable:
            correlation_data = {"risk_multiplier": 1.0, "signal_count": 0, "unavailable": True}
            if req.context.get("criticality") == "critical":
                return RiskResponse(
                    action="BLOCK", score=100.0, confidence=0.0,
                    signals=list(dict.fromkeys([*req.signals, "correlation_unavailable"])),
                    factors={"correlation": correlation_data, "safety_reason": "shared_correlation_unavailable"},
                    explanation="shared correlation unavailable for critical request",
                )
            req.signals = list(dict.fromkeys([*req.signals, "correlation_unavailable"]))

    calibrated_score = calibration.calibrate(raw_score)
    action = matrix.get_action(calibrated_score, confidence)
    decision = safety.process({"action": action, "reason": "risk_engine"})
    final_action = decision["action"]
    if final_action == "MONITOR_ONLY":
        final_action = "MONITOR"

    factors = {
        **base.get("factors", {}),
        "signal_weights": signal_weights,
        "unknown_signals": unknown_signals,
        "correlation": correlation_data,
        "raw_score": round(raw_score, 2),
        "calibrated_score": round(calibrated_score, 2),
        "safety_reason": decision["reason"],
    }
    return RiskResponse(
        action=final_action,
        score=round(calibrated_score, 1),
        confidence=round(confidence, 2),
        signals=list(dict.fromkeys(req.signals)),
        factors=factors,
        explanation=(
            f"raw_score={raw_score:.1f} calibrated_score={calibrated_score:.1f} "
            f"confidence={confidence:.2f} action={final_action}"
        ),
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("RISK_ENGINE_PORT", "8090"))
    uvicorn.run("engine.risk.server:app", host="0.0.0.0", port=port, reload=False)
