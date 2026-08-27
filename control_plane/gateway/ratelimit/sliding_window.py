"""In-process sliding-window limiter used for local control-plane tests and fallback."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class SimpleRateLimiter:
    def __init__(self, window_seconds: int = 60) -> None:
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._requests: dict[tuple[str, str, str], deque[float]] = defaultdict(deque)

    def is_allowed(self, dimension: str, identifier: str, endpoint: str, limit: int = 100) -> dict[str, int | bool]:
        now = time.monotonic()
        key = (dimension, identifier, endpoint)
        with self._lock:
            timestamps = self._requests[key]
            cutoff = now - self.window_seconds
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if len(timestamps) >= limit:
                reset_in = max(1, int(timestamps[0] + self.window_seconds - now))
                return {"allowed": False, "reset_in": reset_in, "remaining": 0}
            timestamps.append(now)
            return {
                "allowed": True,
                "reset_in": max(1, int(timestamps[0] + self.window_seconds - now)),
                "remaining": max(0, limit - len(timestamps)),
            }
