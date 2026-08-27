from threading import Lock


class SafetyLayer:
    """Final guardrail for risk decisions.

    The layer is deliberately fail-closed for malformed decisions and an open
    circuit. A separate monitor-only mode is explicit and must never be the
    production default.
    """

    _VALID_ACTIONS = {"ALLOW", "MONITOR", "CHALLENGE", "BLOCK"}

    def __init__(self, *, mode: str = "production", failure_threshold: int = 5):
        self.mode = mode
        self.circuit_breaker = {
            "state": "CLOSED",
            "failures": 0,
            "threshold": max(1, failure_threshold),
        }
        self._lock = Lock()

    def process(self, decision: dict) -> dict:
        with self._lock:
            if self.mode == "monitor-only":
                return {
                    "action": "MONITOR_ONLY",
                    "blocked": False,
                    "reason": "safety_layer_monitor_only",
                }
            if self.circuit_breaker["state"] == "OPEN":
                return {
                    "action": "BLOCK",
                    "blocked": True,
                    "reason": "safety_circuit_open",
                }

        action = str(decision.get("action", "BLOCK")).upper()
        if action not in self._VALID_ACTIONS:
            return {
                "action": "BLOCK",
                "blocked": True,
                "reason": "invalid_risk_action",
            }
        return {
            "action": action,
            "blocked": action == "BLOCK",
            "reason": decision.get("reason", "risk_decision"),
        }

    def record_failure(self) -> None:
        with self._lock:
            self.circuit_breaker["failures"] += 1
            if self.circuit_breaker["failures"] >= self.circuit_breaker["threshold"]:
                self.circuit_breaker["state"] = "OPEN"

    def record_success(self) -> None:
        with self._lock:
            self.circuit_breaker["failures"] = 0
            self.circuit_breaker["state"] = "CLOSED"
