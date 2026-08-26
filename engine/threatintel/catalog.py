class ThreatIntelCatalog:
    def __init__(self):
        self.threats = {
            "malware": {"severity": "high", "action": "block"},
            "phishing": {"severity": "high", "action": "block"},
            "scanner": {"severity": "medium", "action": "monitor"},
            "botnet": {"severity": "high", "action": "block"},
            "proxy": {"severity": "low", "action": "monitor"},
        }

    def get_severity(self, threat_type: str) -> str:
        return self.threats.get(threat_type, {}).get("severity", "medium")

    def get_action(self, threat_type: str) -> str:
        return self.threats.get(threat_type, {}).get("action", "monitor")

    def list_threats(self):
        return list(self.threats.keys())
