"""Baseline lifecycle: COLLECT → FILTER → VALIDATE → ESTABLISH → MONITOR → UPDATE → ROLLBACK (Section 11.14)."""
from __future__ import annotations

from datetime import UTC, datetime
from math import sqrt
from typing import Any


class BaselineLifecycle:
    PHASES = ["COLLECT", "FILTER", "VALIDATE", "ESTABLISH", "MONITOR", "UPDATE", "ROLLBACK"]

    def __init__(self, min_samples: int = 10, z_threshold: float = 3.0) -> None:
        self.min_samples = min_samples
        self.z_threshold = z_threshold
        self.state: dict[str, list[dict[str, Any]]] = {}
        self.baseline: dict[str, dict[str, Any]] = {}
        self.version: dict[str, int] = {}

    def collect(self, endpoint: str, value: float) -> None:
        self.state.setdefault(endpoint, []).append(
            {"value": float(value), "timestamp": datetime.now(UTC).isoformat()}
        )

    def filter(self, endpoint: str, abs_max: float = 1e6) -> None:
        data = self.state.get(endpoint, [])
        self.state[endpoint] = [d for d in data if abs(d["value"]) < abs_max]

    def validate(self, endpoint: str) -> bool:
        return len(self.state.get(endpoint, [])) >= self.min_samples

    def establish(self, endpoint: str) -> dict[str, Any] | None:
        if not self.validate(endpoint):
            return None
        values = [d["value"] for d in self.state[endpoint]]
        mean = sum(values) / len(values)
        var = sum((v - mean) ** 2 for v in values) / max(len(values) - 1, 1)
        std = sqrt(var) or 1.0
        self.version[endpoint] = self.version.get(endpoint, 0) + 1
        self.baseline[endpoint] = {
            "mean": mean,
            "std": std,
            "sample_count": len(values),
            "version": self.version[endpoint],
            "established_at": datetime.now(UTC).isoformat(),
        }
        return self.baseline[endpoint]

    def monitor(self, endpoint: str, value: float) -> dict[str, Any]:
        b = self.baseline.get(endpoint)
        if not b:
            return {"anomaly": False, "reason": "no_baseline"}
        z = abs(value - b["mean"]) / (b["std"] or 1.0)
        if z > self.z_threshold:
            return {"anomaly": True, "score": z, "version": b["version"]}
        return {"anomaly": False, "score": z, "version": b["version"]}

    def update(self, endpoint: str) -> dict[str, Any] | None:
        self.filter(endpoint)
        return self.establish(endpoint)

    def rollback(self, endpoint: str) -> None:
        self.baseline.pop(endpoint, None)
