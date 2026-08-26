class ThreatIntelScoring:
    def __init__(self):
        self.weights = {
            "malware": 30,
            "phishing": 25,
            "scanner": 15,
            "botnet": 35,
            "proxy": 10,
        }

    def get_score(self, threat_type: str) -> int:
        return self.weights.get(threat_type, 10)

    def calculate_risk(self, threats: list) -> int:
        if not threats:
            return 0
        total = sum(self.get_score(t) for t in threats)
        return min(100, total)

    def get_confidence(self, threat_type: str) -> float:
        confidence_map = {
            "malware": 0.9,
            "phishing": 0.8,
            "scanner": 0.6,
            "botnet": 0.85,
            "proxy": 0.5,
        }
        return confidence_map.get(threat_type, 0.5)
