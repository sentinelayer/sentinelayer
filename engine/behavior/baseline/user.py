from collections import defaultdict
from datetime import datetime, timedelta

class UserBaseline:
    def __init__(self):
        self.user_data = defaultdict(list)

    def add_activity(self, user_id: str, activity: str):
        self.user_data[user_id].append({
            "activity": activity,
            "timestamp": datetime.utcnow().isoformat()
        })
        if len(self.user_data[user_id]) > 100:
            self.user_data[user_id] = self.user_data[user_id][-100:]

    def get_activity_count(self, user_id: str, minutes: int = 60) -> int:
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        activities = self.user_data.get(user_id, [])
        return len([a for a in activities if datetime.fromisoformat(a["timestamp"]) > cutoff])

    def is_anomalous(self, user_id: str, threshold: int = 50) -> bool:
        count = self.get_activity_count(user_id)
        return count > threshold
