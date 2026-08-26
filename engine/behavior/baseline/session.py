from collections import defaultdict
from datetime import datetime


class SessionBaseline:
    def __init__(self):
        self.sessions = defaultdict(list)

    def add_session(self, session_id: str, action: str):
        self.sessions[session_id].append({
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_session_actions(self, session_id: str) -> list:
        return self.sessions.get(session_id, [])

    def is_abnormal(self, session_id: str) -> bool:
        actions = self.get_session_actions(session_id)
        if len(actions) < 3:
            return False
        recent = actions[-5:]
        times = [datetime.fromisoformat(a["timestamp"]) for a in recent]
        gaps = [(times[i+1] - times[i]).seconds for i in range(len(times)-1)]
        if all(g < 2 for g in gaps):
            return True
        return False
