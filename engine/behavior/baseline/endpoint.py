from collections import defaultdict
from datetime import datetime


class EndpointBaseline:
    def __init__(self):
        self.baselines = defaultdict(list)

    def add_observation(self, endpoint: str, value: float):
        self.baselines[endpoint].append({
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        })
        if len(self.baselines[endpoint]) > 100:
            self.baselines[endpoint] = self.baselines[endpoint][-100:]

    def get_baseline(self, endpoint: str) -> float:
        values = [v["value"] for v in self.baselines.get(endpoint, [])]
        if not values:
            return 0.0
        return sum(values) / len(values)

    def get_anomaly_score(self, endpoint: str, value: float) -> float:
        baseline = self.get_baseline(endpoint)
        if baseline == 0:
            return 0.0
        return abs(value - baseline) / baseline
