from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

import redis


class CorrelationUnavailable(RuntimeError):
    """Raised when shared correlation state cannot be read or written."""


class RiskCorrelation:
    def __init__(self, redis_url: str | None = None, require_shared: bool = False):
        self.signals = defaultdict(list)
        self.correlation_window = 60
        self._redis = None
        configured_url = redis_url or os.getenv("REDIS_URL", "").strip()
        if configured_url:
            self._redis = redis.Redis.from_url(configured_url, decode_responses=True)
        elif require_shared:
            raise RuntimeError("REDIS_URL is required for shared risk correlation in production")

    def _key(self, tenant_id: str) -> str:
        return f"sl:risk:correlation:{tenant_id}"

    def add_signal(self, tenant_id: str, signal_type: str, data: dict[str, Any]):
        if not tenant_id:
            return
        now = time.time()
        entry = json.dumps({"type": signal_type, "data": data, "timestamp": now}, sort_keys=True)
        if self._redis is not None:
            try:
                key = self._key(tenant_id)
                pipe = self._redis.pipeline(transaction=True)
                pipe.zremrangebyscore(key, 0, now - self.correlation_window)
                pipe.zadd(key, {entry: now})
                pipe.expire(key, self.correlation_window + 5)
                pipe.execute()
            except redis.RedisError as exc:
                raise CorrelationUnavailable("shared correlation store unavailable") from exc
            return
        self.signals[tenant_id].append({
            "type": signal_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self._cleanup(tenant_id)

    def _cleanup(self, tenant_id: str):
        cutoff = datetime.utcnow() - timedelta(seconds=self.correlation_window)
        self.signals[tenant_id] = [
            s for s in self.signals[tenant_id]
            if datetime.fromisoformat(s["timestamp"]) > cutoff
        ]

    def _shared_signals(self, tenant_id: str) -> list[dict[str, Any]]:
        assert self._redis is not None
        now = time.time()
        try:
            key = self._key(tenant_id)
            pipe = self._redis.pipeline(transaction=True)
            pipe.zremrangebyscore(key, 0, now - self.correlation_window)
            pipe.zrange(key, 0, -1)
            values = pipe.execute()[1]
        except redis.RedisError as exc:
            raise CorrelationUnavailable("shared correlation store unavailable") from exc
        signals: list[dict[str, Any]] = []
        for raw in values:
            try:
                parsed = json.loads(raw)
            except (TypeError, json.JSONDecodeError):
                continue
            if isinstance(parsed, dict) and isinstance(parsed.get("type"), str):
                signals.append(parsed)
        return signals

    def correlate(self, tenant_id: str) -> dict[str, Any]:
        if not tenant_id:
            return {"risk_multiplier": 1.0, "signal_count": 0, "unique_types": 0, "types": []}
        signals = self._shared_signals(tenant_id) if self._redis is not None else self.signals.get(tenant_id, [])
        if not signals:
            return {"risk_multiplier": 1.0, "signal_count": 0, "unique_types": 0, "types": []}
        types = sorted({s["type"] for s in signals})
        multiplier = 1.0
        if len(types) >= 5:
            multiplier = 2.0
        elif len(types) >= 3:
            multiplier = 1.5
        return {
            "risk_multiplier": multiplier,
            "signal_count": len(signals),
            "unique_types": len(types),
            "types": types,
        }
