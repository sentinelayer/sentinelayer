"""Explainability — returns stored decisions; empty until risk engine records one."""
from fastapi import APIRouter, HTTPException
from typing import Any, Optional

router = APIRouter(prefix="/explainability", tags=["explainability"])

# Runtime store (not demo seed)
DECISIONS: list[dict[str, Any]] = []


@router.get("/latest")
async def get_latest_explainability():
    if not DECISIONS:
        return {"error": "No decisions recorded yet"}
    return DECISIONS[-1]


@router.get("/")
@router.get("")
async def get_explainability(decision_id: Optional[str] = None):
    if decision_id:
        for d in DECISIONS:
            if d.get("id") == decision_id:
                return d
        raise HTTPException(status_code=404, detail="Decision not found")
    return DECISIONS


@router.get("/decision/{decision_id}")
async def get_decision_explainability(decision_id: str):
    for d in DECISIONS:
        if d.get("id") == decision_id:
            return {
                **d,
                "what": f"Decision was {d.get('action')}",
                "why": d.get("reason"),
                "who": "system",
                "when": d.get("timestamp"),
                "score": d.get("risk_score"),
            }
    raise HTTPException(status_code=404, detail="Decision not found")
