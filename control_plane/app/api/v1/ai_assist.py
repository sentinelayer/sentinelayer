"""AI assist — off-path only. Never blocks request path."""
from datetime import UTC, datetime

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/ai", tags=["ai"])


class ExplainRequest(BaseModel):
    # This is a bounded formatter of caller-supplied risk data, not an LLM verdict.
    decision: str = Field(min_length=1, max_length=40)
    score: float = Field(ge=0, le=100, allow_inf_nan=False)
    signals: list[str] = Field(default_factory=list, max_length=32)
    context: dict = Field(default_factory=dict)


@router.post("/explain")
async def explain_decision(
    req: ExplainRequest,
    x_tenant_id: str | None = Header(None),
):
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="Missing tenant ID")
    # Deterministic local explanation (no external LLM call on request path)
    reasons = []
    if req.score >= 80:
        reasons.append("High risk score indicates likely attack or policy violation.")
    elif req.score >= 50:
        reasons.append("Elevated risk; monitor or step-up auth recommended.")
    else:
        reasons.append("Risk within normal baseline.")
    for s in req.signals[:8]:
        reasons.append(f"Signal: {s}")
    return {
        "explanation": " ".join(reasons),
        "decision": req.decision,
        "score": req.score,
        "mode": "off-path-local",
        "advisory_only": True,
        "input_origin": "caller-supplied",
        "generated_at": datetime.now(UTC).isoformat(),
    }
