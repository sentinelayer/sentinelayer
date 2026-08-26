from fastapi import APIRouter
from datetime import datetime
import random

router = APIRouter(prefix="/explainability", tags=["explainability"])

DECISIONS = [
    {
        "id": "dec-001",
        "action": "ALLOW",
        "risk_score": 15,
        "reason": "Low risk score, normal traffic",
        "factors": {"failed_attempts": 0, "suspicious_ip": False},
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "id": "dec-002",
        "action": "BLOCK",
        "risk_score": 85,
        "reason": "SQL injection pattern detected",
        "factors": {"sql_injection": 30, "xss": 25, "rate_limit": 20},
        "timestamp": datetime.utcnow().isoformat()
    }
]

@router.get("/latest")
async def get_latest_explainability():
    return DECISIONS[-1] if DECISIONS else {"error": "No decisions"}

@router.get("/")
async def get_explainability(decision_id: str = None):
    if decision_id:
        for d in DECISIONS:
            if d["id"] == decision_id:
                return d
        return {"error": "Decision not found"}
    return DECISIONS

@router.get("/decision/{decision_id}")
async def get_decision_explainability(decision_id: str):
    for d in DECISIONS:
        if d["id"] == decision_id:
            return {
                **d,
                "what": f"Decision was {d['action']}",
                "why": d["reason"],
                "who": "system",
                "when": d["timestamp"],
                "score": d["risk_score"]
            }
    return {"error": "Decision not found"}
