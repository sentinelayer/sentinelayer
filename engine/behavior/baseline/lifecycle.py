from datetime import datetime, timedelta

class BaselineLifecycle:
    def __init__(self):
        self.phases = ["COLLECT", "FILTER", "VALIDATE", "ESTABLISH", "MONITOR", "UPDATE", "ROLLBACK"]
        self.state = {}
        self.baseline = {}

    def collect(self, endpoint: str, value: float):
        if endpoint not in self.state:
            self.state[endpoint] = []
        self.state[endpoint].append({"value": value, "timestamp": datetime.utcnow().isoformat()})

    def filter(self, endpoint: str):
        if endpoint in self.state:
            data = self.state[endpoint]
            threshold = 3
            filtered = [d for d in data if abs(d["value"]) < threshold]
            self.state[endpoint] = filtered

    def validate(self, endpoint: str):
        if endpoint in self.state and len(self.state[endpoint]) >= 10:
            return True
        return False

    def establish(self, endpoint: str):
        if self.validate(endpoint):
            values = [d["value"] for d in self.state[endpoint]]
            self.baseline[endpoint] = {
                "mean": sum(values) / len(values),
                "std": 1.0,
                "sample_count": len(values),
                "established_at": datetime.utcnow().isoformat()
            }

    def monitor(self, endpoint: str, value: float):
        if endpoint in self.baseline:
            mean = self.baseline[endpoint]["mean"]
            std = self.baseline[endpoint]["std"]
            if abs(value - mean) > 3 * std:
                return {"anomaly": True, "score": abs(value - mean) / std}
        return {"anomaly": False}

    def update(self, endpoint: str):
        if endpoint in self.state:
            self.establish(endpoint)

    def rollback(self, endpoint: str):
        if endpoint in self.baseline:
            del self.baseline[endpoint]
