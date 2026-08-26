class BehaviorEngine:
    def __init__(self):
        self.user_behavior = {}
    
    def track(self, context: dict):
        user_id = context.get("user_id")
        if user_id:
            if user_id not in self.user_behavior:
                self.user_behavior[user_id] = {"count": 0}
            self.user_behavior[user_id]["count"] += 1
    
    def get_behavior(self, user_id: str) -> dict:
        return self.user_behavior.get(user_id, {"count": 0})

behavior_engine = BehaviorEngine()
