from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List

class BehaviorEngine:
    def __init__(self):
        self.user_behavior = defaultdict(lambda: {"count": 0, "last_seen": None, "actions": []})
        self.session_behavior = defaultdict(lambda: {"count": 0, "last_seen": None})
        self.baseline = defaultdict(lambda: {"avg": 0, "std": 0, "samples": []})

    def track(self, context: dict):
        user_id = context.get("user_id")
        if not user_id:
            return

        self.user_behavior[user_id]["count"] += 1
        self.user_behavior[user_id]["last_seen"] = datetime.utcnow().isoformat()
        self.user_behavior[user_id]["actions"].append({
            "action": context.get("action", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        })

        if len(self.user_behavior[user_id]["actions"]) > 100:
            self.user_behavior[user_id]["actions"] = self.user_behavior[user_id]["actions"][-100:]

    def detect_anomaly(self, user_id: str) -> dict:
        if user_id not in self.user_behavior:
            return {"is_anomaly": False, "reason": "No behavior data"}

        data = self.user_behavior[user_id]
        recent_count = len([a for a in data["actions"] if datetime.fromisoformat(a["timestamp"]) > datetime.utcnow() - timedelta(minutes=5)])

        if recent_count > 50:
            return {"is_anomaly": True, "reason": "Excessive requests in short period", "confidence": 0.8}
        if recent_count > 20:
            return {"is_anomaly": True, "reason": "Elevated request rate", "confidence": 0.6}

        return {"is_anomaly": False, "reason": "Normal behavior"}

    def get_behavior(self, user_id: str) -> dict:
        return self.user_behavior.get(user_id, {"count": 0, "last_seen": None, "actions": []})

behavior_engine = BehaviorEngine()
