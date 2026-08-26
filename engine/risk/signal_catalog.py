class SignalCatalog:
    def __init__(self):
        self.signals = {
            "waf_block": {"weight": 30, "description": "WAF blocked a request"},
            "rate_limit_exceeded": {"weight": 20, "description": "Rate limit exceeded"},
            "auth_failure": {"weight": 15, "description": "Authentication failure"},
            "suspicious_ip": {"weight": 25, "description": "Suspicious IP detected"},
            "xss_attempt": {"weight": 35, "description": "XSS attempt detected"},
        }

    def get_weight(self, signal_type: str) -> int:
        return self.signals.get(signal_type, {}).get("weight", 10)

    def get_description(self, signal_type: str) -> str:
        return self.signals.get(signal_type, {}).get("description", "Unknown signal")

    def list_signals(self):
        return list(self.signals.keys())
