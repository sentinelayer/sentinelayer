from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

import redis
from engine.risk.signal_catalog import SignalCatalog


class CorrelationUnavailable(RuntimeError):
    """Raised when shared correlation state cannot be read or written."""


# One last-seen entry per catalog type and at most 61 one-second counters.
# Preserve legacy JSON entries until their existing 60-second window expires.
_ADD_SIGNAL = """
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, ARGV[2])
redis.call('ZADD', KEYS[1], ARGV[1], 'type:' .. ARGV[3])
redis.call('HINCRBY', KEYS[2], ARGV[4], 1)
for _, bucket in ipairs(redis.call('HKEYS', KEYS[2])) do
  if tonumber(bucket) < tonumber(ARGV[5]) then redis.call('HDEL', KEYS[2], bucket) end
end
redis.call('EXPIRE', KEYS[1], ARGV[6])
redis.call('EXPIRE', KEYS[2], ARGV[6])
return 1
"""

_OBSERVE_SIGNALS = """
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, ARGV[2])
for i = 6, #ARGV do
  redis.call('ZADD', KEYS[1], ARGV[1], 'type:' .. ARGV[i])
end
if #ARGV > 5 then redis.call('HINCRBY', KEYS[2], ARGV[3], #ARGV - 5) end
for _, bucket in ipairs(redis.call('HKEYS', KEYS[2])) do
  if tonumber(bucket) < tonumber(ARGV[4]) then redis.call('HDEL', KEYS[2], bucket) end
end
redis.call('EXPIRE', KEYS[1], ARGV[5])
redis.call('EXPIRE', KEYS[2], ARGV[5])
return {redis.call('ZRANGE', KEYS[1], 0, -1), redis.call('HGETALL', KEYS[2])}
"""

class RiskCorrelation:
    def __init__(self, redis_url: str | None = None, require_shared: bool = False):
        self.signals = defaultdict(list)
        self.correlation_window = 60
        self._redis = None
        configured_url = redis_url or os.getenv("REDIS_URL", "").strip()
        if configured_url:
            self._redis = redis.Redis.from_url(configured_url, decode_responses=True, socket_connect_timeout=0.2,
                socket_timeout=0.2, retry_on_timeout=False)
        elif require_shared:
            raise RuntimeError("REDIS_URL is required for shared risk correlation in production")

    def _key(self, tenant_id: str) -> str:
        return f"sl:risk:correlation:{tenant_id}"

    def add_signal(self, tenant_id: str, signal_type: str, data: dict[str, Any]):
        if not tenant_id or signal_type not in SignalCatalog().signals:
            return
        now = time.time()
        if self._redis is not None:
            try:
                key = self._key(tenant_id)
                self._redis.eval(_ADD_SIGNAL, 2, key, key + ":counts", now,
                    now - self.correlation_window, signal_type, int(now),
                    int(now - self.correlation_window), self.correlation_window + 5)
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

    def _shared_signals(self, tenant_id: str) -> tuple[list[dict[str, Any]], int]:
        assert self._redis is not None
        now = time.time()
        try:
            key = self._key(tenant_id)
            pipe = self._redis.pipeline(transaction=True)
            pipe.zremrangebyscore(key, 0, now - self.correlation_window)
            pipe.zrange(key, 0, -1)
            pipe.hgetall(key + ":counts")
            result = pipe.execute()
            values, counters = result[1], result[2]
        except redis.RedisError as exc:
            raise CorrelationUnavailable("shared correlation store unavailable") from exc
        signals: list[dict[str, Any]] = []
        legacy_count = 0
        for raw in values:
            if raw.startswith("type:"):
                signals.append({"type": raw[5:]})
                continue
            try:
                parsed = json.loads(raw)
            except (TypeError, json.JSONDecodeError):
                continue
            if isinstance(parsed, dict) and isinstance(parsed.get("type"), str):
                signals.append(parsed)
                legacy_count += 1
        count = legacy_count + sum(int(value) for bucket, value in counters.items()
                                   if int(bucket) >= int(now - self.correlation_window))
        return signals, count

    def observe(self, tenant_id: str, signal_types: list[str], data: dict[str, Any]) -> dict[str, Any]:
        if not tenant_id or self._redis is None:
            for signal in dict.fromkeys(signal_types):
                self.add_signal(tenant_id, signal, data)
            return self.correlate(tenant_id)
        now = time.time()
        known = [signal for signal in dict.fromkeys(signal_types) if signal in SignalCatalog().signals]
        key = self._key(tenant_id)
        try:
            values, flat = self._redis.eval(_OBSERVE_SIGNALS, 2, key, key + ":counts", now,
                now - self.correlation_window, int(now), int(now - self.correlation_window),
                self.correlation_window + 5, *known)
        except redis.RedisError as exc:
            raise CorrelationUnavailable("shared correlation store unavailable") from exc
        types = set()
        legacy_count = 0
        for raw in values:
            if raw.startswith("type:"):
                types.add(raw[5:])
            else:
                try:
                    item = json.loads(raw)
                except (TypeError, json.JSONDecodeError):
                    continue
                if isinstance(item, dict) and isinstance(item.get("type"), str):
                    types.add(item["type"])
                    legacy_count += 1
        count = legacy_count + sum(int(value) for value in flat[1::2])
        multiplier = 2.0 if len(types) >= 5 else 1.5 if len(types) >= 3 else 1.0
        return {"risk_multiplier": multiplier, "signal_count": count, "unique_types": len(types),
                "types": sorted(types), "count_precision_seconds": 1}

    def correlate(self, tenant_id: str) -> dict[str, Any]:
        if not tenant_id:
            return {"risk_multiplier": 1.0, "signal_count": 0, "unique_types": 0, "types": []}
        if self._redis is not None:
            signals, signal_count = self._shared_signals(tenant_id)
        else:
            self._cleanup(tenant_id)
            signals = self.signals.get(tenant_id, [])
            signal_count = len(signals)
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
            "signal_count": signal_count,
            "count_precision_seconds": 1 if self._redis is not None else 0,
            "unique_types": len(types),
            "types": types,
        }
