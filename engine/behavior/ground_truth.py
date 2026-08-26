class GroundTruth:
    def __init__(self):
        self.labels = {}

    def label(self, user_id: str, behavior: str, is_malicious: bool):
        if user_id not in self.labels:
            self.labels[user_id] = []
        self.labels[user_id].append({
            "behavior": behavior,
            "is_malicious": is_malicious,
            "timestamp": "now"
        })

    def get_label(self, user_id: str) -> list:
        return self.labels.get(user_id, [])

    def get_malicious_count(self, user_id: str) -> int:
        return len([l for l in self.labels.get(user_id, []) if l["is_malicious"]])

    def get_benign_count(self, user_id: str) -> int:
        return len([l for l in self.labels.get(user_id, []) if not l["is_malicious"]])
