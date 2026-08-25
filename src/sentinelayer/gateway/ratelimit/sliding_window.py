import time
import hashlib
import redis
import json
from typing import Optional, Dict, Tuple
from functools import lru_cache

class RedisSlidingWindowRateLimiter:
    """Redis-based sliding window rate limiter"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", default_window: int = 60):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.default_window = default_window
        self._lua_script = None
        self._load_lua_script()
    
    def _load_lua_script(self):
        """Load Lua script for atomic operations"""
        script = """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local window = tonumber(ARGV[2])
            local limit = tonumber(ARGV[3])
            local window_start = now - window
            
            -- Remove old entries
            redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
            
            -- Count current entries
            local current = redis.call('ZCARD', key)
            
            if current >= limit then
                local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
                return {0, current, oldest[2] or 0}
            end
            
            -- Add new request
            redis.call('ZADD', key, now, tostring(now) .. ':' .. tostring(math.random()))
            redis.call('EXPIRE', key, window + 5)
            
            return {1, current + 1, 0}
        """
        self._lua_script = self.redis.register_script(script)
    
    def _get_key(self, prefix: str, identifier: str, endpoint: str = "") -> str:
        """Generate Redis key"""
        hashed = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        endpoint_slug = endpoint.replace("/", "_").strip("_")
        if endpoint_slug:
            return f"ratelimit:{prefix}:{hashed}:{endpoint_slug}"
        return f"ratelimit:{prefix}:{hashed}"
    
    def _get_default_limit(self, dimension: str) -> Tuple[int, int]:
        """Get default limits per dimension"""
        limits = {
            "ip": (60, 100),      # 100 req/min per IP
            "user": (60, 200),    # 200 req/min per user
            "api_key": (60, 500), # 500 req/min per API key
            "tenant": (60, 5000), # 5000 req/min per tenant
        }
        return limits.get(dimension, (self.default_window, 100))
    
    def is_allowed(
        self,
        dimension: str,
        identifier: str,
        endpoint: str = "",
        limit_override: Optional[int] = None,
        window_override: Optional[int] = None
    ) -> Dict:
        """Check if request is allowed"""
        key = self._get_key(dimension, identifier, endpoint)
        now = time.time()
        
        # Get limit
        if limit_override and window_override:
            limit = limit_override
            window = window_override
        else:
            window, limit = self._get_default_limit(dimension)
        
        # Execute Lua script atomically
        try:
            result = self._lua_script(
                keys=[key],
                args=[str(now), str(window), str(limit)]
            )
            
            allowed = bool(result[0])
            current_count = int(result[1])
            oldest_timestamp = float(result[2])
            
            remaining = max(0, limit - current_count)
            
            # Calculate reset time
            if oldest_timestamp > 0:
                reset_in = int(oldest_timestamp + window - now)
            else:
                reset_in = int(window)
            
            return {
                "allowed": allowed,
                "remaining": remaining,
                "reset_in": max(0, reset_in),
                "limit": limit,
                "window": window,
                "dimension": dimension,
                "current": current_count
            }
            
        except Exception as e:
            # Redis unavailable -> fail-open
            print(f"Rate limiter error: {e}")
            return {
                "allowed": True,
                "remaining": 999,
                "reset_in": 0,
                "limit": 999,
                "window": 60,
                "dimension": dimension,
                "error": str(e)
            }
    
    def get_usage(self, dimension: str, identifier: str, endpoint: str = "") -> Dict:
        """Get current usage without incrementing"""
        key = self._get_key(dimension, identifier, endpoint)
        try:
            count = self.redis.zcount(key, time.time() - 60, time.time())
            _, limit = self._get_default_limit(dimension)
            return {
                "current": count,
                "limit": limit,
                "remaining": max(0, limit - count)
            }
        except:
            return {"current": 0, "limit": 0, "remaining": 0}

# Simple rate limiter (fallback when Redis not available)
class SimpleRateLimiter:
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, dimension: str, identifier: str, endpoint: str = "", limit: int = 100, window: int = 60) -> Dict:
        key = f"{dimension}:{identifier}:{endpoint}"
        now = time.time()
        
        if key in self.requests:
            self.requests[key] = [t for t in self.requests[key] if t > now - window]
        else:
            self.requests[key] = []
        
        if len(self.requests[key]) >= limit:
            return {
                "allowed": False,
                "remaining": 0,
                "reset_in": int(window),
                "limit": limit,
                "window": window,
                "dimension": dimension
            }
        
        self.requests[key].append(now)
        return {
            "allowed": True,
            "remaining": limit - len(self.requests[key]) - 1,
            "reset_in": int(window),
            "limit": limit,
            "window": window,
            "dimension": dimension
        }
