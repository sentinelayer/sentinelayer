import os
from typing import Dict

class SafeMode:
    def __init__(self):
        self.mode = os.getenv("DECISION_MODE", "production")
        self.override_enabled = False
        self.override_reason = None
        self.circuit_breaker = {"state": "CLOSED", "failures": 0, "threshold": 5}

    def process_decision(self, decision: Dict) -> Dict:
        if self.mode == "monitor-only":
            return {
                "action": "MONITOR_ONLY",
                "blocked": False,
                "reason": "Monitor-only mode enabled"
            }

        if self.mode == "safe":
            if decision.get("action") == "BLOCK":
                return {
                    "action": "CHALLENGE",
                    "blocked": False,
                    "reason": "Safe mode: BLOCK converted to CHALLENGE"
                }

        if self.circuit_breaker["state"] == "OPEN":
            return {
                "action": "ALLOW",
                "blocked": False,
                "reason": "Circuit breaker OPEN - allowing traffic"
            }

        return {
            "action": decision.get("action", "ALLOW"),
            "blocked": decision.get("action") == "BLOCK",
            "reason": "Normal decision mode"
        }

    def record_failure(self):
        self.circuit_breaker["failures"] += 1
        if self.circuit_breaker["failures"] >= self.circuit_breaker["threshold"]:
            self.circuit_breaker["state"] = "OPEN"

    def reset_circuit(self):
        self.circuit_breaker["state"] = "CLOSED"
        self.circuit_breaker["failures"] = 0

safe_mode = SafeMode()
