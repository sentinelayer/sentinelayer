from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict

class ApplicationContext:
    def __init__(self):
        self.user_sessions = defaultdict(list)
        self.business_flows = {}
    
    def track_flow(self, user_id: str, action: str, data: Dict):
        self.user_sessions[user_id].append({
            "action": action,
            "data": data,
            "timestamp": datetime.utcnow()
        })
        
        if len(self.user_sessions[user_id]) > 100:
            self.user_sessions[user_id] = self.user_sessions[user_id][-100:]
    
    def detect_abuse(self, user_id: str) -> Dict:
        history = self.user_sessions.get(user_id, [])
        if len(history) < 3:
            return {"abuse_detected": False, "reason": "insufficient_history"}
        
        # Check for rapid sequence
        recent = history[-5:]
        if len(recent) == 5:
            times = [r["timestamp"] for r in recent]
            gaps = [(times[i+1] - times[i]).seconds for i in range(len(times)-1)]
            if all(g < 5 for g in gaps):
                return {
                    "abuse_detected": True,
                    "reason": "rapid_sequence",
                    "confidence": 0.8
                }
        
        # Check for action repetition
        actions = [h["action"] for h in history[-10:]]
        if len(set(actions)) <= 2:
            return {
                "abuse_detected": True,
                "reason": "action_repetition",
                "confidence": 0.6
            }
        
        return {"abuse_detected": False, "reason": "normal_behavior"}

context_analyzer = ApplicationContext()
