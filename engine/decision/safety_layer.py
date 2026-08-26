class SafetyLayer:
    def __init__(self):
        self.mode = "production"
        self.circuit_breaker = {"state": "CLOSED", "failures": 0, "threshold": 5}

    def process(self, decision: dict) -> dict:
        if self.mode == "monitor-only":
            return {"action": "MONITOR_ONLY", "blocked": False}
        if self.circuit_breaker["state"] == "OPEN":
            return {"action": "ALLOW", "blocked": False}
        return {"action": decision.get("action", "ALLOW"), "blocked": decision.get("action") == "BLOCK"}

    def record_failure(self):
        self.circuit_breaker["failures"] += 1
        if self.circuit_breaker["failures"] >= self.circuit_breaker["threshold"]:
            self.circuit_breaker["state"] = "OPEN"
