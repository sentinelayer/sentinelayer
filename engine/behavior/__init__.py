"""Behavior Engine — track, baseline, sequence, frequency anomaly (Section 11)."""
from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from math import sqrt
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).isoformat()


class BehaviorEngine:
    def __init__(self, window_minutes: int = 5, max_actions: int = 200) -> None:
        self.window = timedelta(minutes=window_minutes)
        self.max_actions = max_actions
        self.user_behavior: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "last_seen": None, "actions": deque(maxlen=self.max_actions)}
        )
        self.endpoint_counts: dict[str, deque] = defaultdict(lambda: deque(maxlen=500))
        self.sequences: dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self.baselines: dict[str, dict[str, float]] = {}

    def track(self, context: dict[str, Any]) -> None:
        user_id = context.get("user_id") or context.get("session_id") or "anon"
        endpoint = context.get("endpoint") or context.get("action") or "unknown"
        ts = _now()
        entry = {"action": endpoint, "timestamp": _iso(ts), "tenant_id": context.get("tenant_id", "")}
        ub = self.user_behavior[user_id]
        ub["count"] += 1
        ub["last_seen"] = _iso(ts)
        ub["actions"].append(entry)
        self.endpoint_counts[endpoint].append(ts.timestamp())
        seq_key = f"{context.get('tenant_id', '')}:{user_id}"
        self.sequences[seq_key].append(endpoint)

    def _count_in_window(self, actions: deque, window: timedelta) -> int:
        cutoff = _now() - window
        n = 0
        for a in actions:
            try:
                t = datetime.fromisoformat(a["timestamp"].replace("Z", "+00:00"))
                if t.tzinfo is None:
                    t = t.replace(tzinfo=timezone.utc)
                if t > cutoff:
                    n += 1
            except Exception:
                continue
        return n

    def detect_frequency_anomaly(self, user_id: str) -> dict[str, Any]:
        data = self.user_behavior.get(user_id)
        if not data:
            return {"is_anomaly": False, "reason": "no_data", "confidence": 0.0, "signals": []}
        recent = self._count_in_window(data["actions"], self.window)
        signals: list[str] = []
        if recent > 50:
            signals.append("freq_critical")
            return {"is_anomaly": True, "reason": "excessive_requests_5m", "confidence": 0.85, "signals": signals, "count": recent}
        if recent > 20:
            signals.append("freq_elevated")
            return {"is_anomaly": True, "reason": "elevated_request_rate_5m", "confidence": 0.65, "signals": signals, "count": recent}
        return {"is_anomaly": False, "reason": "normal", "confidence": 0.4, "signals": [], "count": recent}

    def detect_sequence_abuse(self, tenant_id: str, user_id: str, fraud_patterns: list[list[str]] | None = None) -> dict[str, Any]:
        """Business-flow abuse: sequence of otherwise-legit steps (Section 11.23)."""
        fraud_patterns = fraud_patterns or [
            ["login", "add_payment", "coupon", "refund"],
            ["login", "password_reset", "password_reset", "password_reset"],
        ]
        seq = list(self.sequences.get(f"{tenant_id}:{user_id}", []))
        if len(seq) < 2:
            return {"is_anomaly": False, "reason": "short_sequence", "confidence": 0.0, "signals": []}
        joined = " > ".join(seq[-10:])
        for pat in fraud_patterns:
            if self._subsequence(seq, pat):
                return {
                    "is_anomaly": True,
                    "reason": "business_flow_abuse",
                    "confidence": 0.75,
                    "signals": ["sequence_fraud"],
                    "pattern": pat,
                    "observed": joined,
                }
        return {"is_anomaly": False, "reason": "no_fraud_pattern", "confidence": 0.3, "signals": []}

    @staticmethod
    def _subsequence(hay: list[str], needle: list[str]) -> bool:
        if not needle:
            return False
        i = 0
        for item in hay:
            if item == needle[i] or item.endswith(needle[i]) or needle[i] in item:
                i += 1
                if i == len(needle):
                    return True
        return False

    def establish_baseline(self, key: str, values: list[float]) -> dict[str, float]:
        if len(values) < 5:
            return {}
        mean = sum(values) / len(values)
        var = sum((v - mean) ** 2 for v in values) / max(len(values) - 1, 1)
        std = sqrt(var) or 1.0
        self.baselines[key] = {"mean": mean, "std": std, "n": float(len(values))}
        return self.baselines[key]

    def monitor_baseline(self, key: str, value: float, z_threshold: float = 3.0) -> dict[str, Any]:
        b = self.baselines.get(key)
        if not b:
            return {"anomaly": False, "reason": "no_baseline"}
        z = abs(value - b["mean"]) / (b["std"] or 1.0)
        if z > z_threshold:
            return {"anomaly": True, "z": z, "reason": "baseline_deviation", "signals": ["baseline_z"]}
        return {"anomaly": False, "z": z, "reason": "within_baseline"}

    def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """Full pass: track + frequency + sequence → signals for Risk Engine."""
        self.track(context)
        user_id = context.get("user_id") or context.get("session_id") or "anon"
        tenant_id = context.get("tenant_id") or ""
        freq = self.detect_frequency_anomaly(user_id)
        seq = self.detect_sequence_abuse(tenant_id, user_id)
        signals: list[str] = []
        signals.extend(freq.get("signals") or [])
        signals.extend(seq.get("signals") or [])
        is_anomaly = bool(freq.get("is_anomaly") or seq.get("is_anomaly"))
        confidence = max(float(freq.get("confidence") or 0), float(seq.get("confidence") or 0))
        return {
            "is_anomaly": is_anomaly,
            "confidence": confidence,
            "signals": signals,
            "frequency": freq,
            "sequence": seq,
        }

    def get_behavior(self, user_id: str) -> dict[str, Any]:
        raw = self.user_behavior.get(user_id)
        if not raw:
            return {"count": 0, "last_seen": None, "actions": []}
        return {
            "count": raw["count"],
            "last_seen": raw["last_seen"],
            "actions": list(raw["actions"]),
        }


behavior_engine = BehaviorEngine()
