import os
import redis
import time
import hashlib
from typing import Dict, Optional

class RedisSlidingWindowRateLimiter:
    def __init__(self, redis_url: str = None):
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    def is_allowed(self, dimension: str, identifier: str, endpoint: str = "", 
                   limit: Optional[int] = None, window: Optional[int] = None) -> Dict:
        key = f"ratelimit:{dimension}:{hashlib.sha256(identifier.encode()).hexdigest()[:16]}:{endpoint}"
        now = time.time()
        window = window or 60
        limit = limit or 100
        window_start = now - window
        
        self.redis.zremrangebyscore(key, 0, window_start)
        current = self.redis.zcard(key)
        
        if current >= limit:
            return {"allowed": False, "remaining": 0, "reset_in": window}
        
        self.redis.zadd(key, {str(now): now})
        self.redis.expire(key, window + 5)
        return {"allowed": True, "remaining": limit - current - 1, "reset_in": window}

class SimpleRateLimiter:
    """Fallback rate limiter (in-memory)"""
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, dimension: str, identifier: str, endpoint: str = "", 
                   limit: Optional[int] = None, window: Optional[int] = None) -> Dict:
        key = f"{dimension}:{identifier}:{endpoint}"
        now = time.time()
        window = window or 60
        limit = limit or 100
        
        if key in self.requests:
            self.requests[key] = [t for t in self.requests[key] if t > now - window]
        else:
            self.requests[key] = []
        
        if len(self.requests[key]) >= limit:
            return {"allowed": False, "remaining": 0, "reset_in": window}
        
        self.requests[key].append(now)
        return {"allowed": True, "remaining": limit - len(self.requests[key]) - 1, "reset_in": window}

# Auto-select: Redis jika tersedia, fallback ke Simple
try:
    _limiter = RedisSlidingWindowRateLimiter()
    _limiter.redis.ping()
    print("✅ Using Redis rate limiter")
    get_rate_limiter = lambda: _limiter
except Exception as e:
    print("⚠️ Redis not available, using simple rate limiter")
    _limiter = SimpleRateLimiter()
    get_rate_limiter = lambda: _limiter
