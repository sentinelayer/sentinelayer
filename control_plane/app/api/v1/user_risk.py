from fastapi import APIRouter
from datetime import datetime
import random

router = APIRouter(prefix="/user-risk", tags=["user-risk"])

USERS = [
    {"user_id": "user-001", "email": "alice@test.com", "risk_score": 12, "status": "active"},
    {"user_id": "user-002", "email": "bob@test.com", "risk_score": 45, "status": "active"},
    {"user_id": "user-003", "email": "charlie@test.com", "risk_score": 78, "status": "suspicious"},
    {"user_id": "user-004", "email": "diana@test.com", "risk_score": 8, "status": "active"},
    {"user_id": "user-005", "email": "eve@test.com", "risk_score": 92, "status": "blocked"},
]

@router.get("/")
async def get_user_risk():
    return USERS

@router.get("/{user_id}")
async def get_user_risk_detail(user_id: str):
    for u in USERS:
        if u["user_id"] == user_id:
            return {
                **u,
                "last_activity": datetime.utcnow().isoformat(),
                "factors": {
                    "failed_attempts": random.randint(0, 10),
                    "suspicious_ip": random.choice([True, False]),
                    "unusual_time": random.choice([True, False])
                }
            }
    return {"error": "User not found"}
