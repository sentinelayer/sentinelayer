import time
import hashlib
from typing import Optional, Dict, Tuple
from redis import Redis
import json

class RateLimitConfig:
    """Resource-cost-aware rate limits (Section 10.25)"""
    
    # Default limits per dimension
    DEFAULTS = {
        "ip": {"window": 60, "limit": 100},      # 100 req/min per IP
        "user": {"window": 60, "limit": 200},    # 200 req/min per user
        "api_key": {"window": 60, "limit": 500}, # 500 req/min per API key
        "tenant": {"window": 60, "limit": 5000}, # 5000 req/min per tenant
    }
    
    # Endpoint-specific limits (resource-cost-aware)
    ENDPOINT_LIMITS = {
        "/health": {"window": 60, "limit": 1000},        # Cheap
        "/api/v1/checkout": {"window": 60, "limit": 10}, # Expensive
        "/api/v1/login": {"window": 60, "limit": 5},     # Security-sensitive
        "/api/v1/orders": {"window": 60, "limit": 50},
        "/api/v1/webhook": {"window": 60, "limit": 20},
    }

class RedisSlidingWindowRateLimiter:
    """Implementasi sliding window dengan Redis (Section 10.10)"""
    
    def __init__(self, redis_client: Redis, default_window: int = 60):
        self.redis = redis_client
        self.default_window = default_window
        
    def _get_key(self, prefix: str, identifier: str, endpoint: str = "") -> str:
        """Generate Redis key dengan endpoint context"""
        # Hash identifier biar konsisten
        hashed = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        endpoint_slug = endpoint.replace("/", "_").strip("_")
        if endpoint_slug:
            return f"ratelimit:{prefix}:{hashed}:{endpoint_slug}"
        return f"ratelimit:{prefix}:{hashed}"
    
    def _get_limit(self, endpoint: str, dimension: str) -> Tuple[int, int]:
        """Dapatkan limit berdasarkan endpoint dan dimension (Section 10.25)"""
        # Cek endpoint-specific limit dulu
        if endpoint in RateLimitConfig.ENDPOINT_LIMITS:
            config = RateLimitConfig.ENDPOINT_LIMITS[endpoint]
            return config["window"], config["limit"]
        
        # Fallback ke default per dimension
        if dimension in RateLimitConfig.DEFAULTS:
            config = RateLimitConfig.DEFAULTS[dimension]
            return config["window"], config["limit"]
        
        # Ultimate fallback
        return self.default_window, 100
    
    def is_allowed(
        self,
        dimension: str,
        identifier: str,
        endpoint: str = "",
        limit_override: Optional[int] = None,
        window_override: Optional[int] = None
    ) -> Dict[str, any]:
        """Check if request is allowed (sliding window)
        
        Returns:
            {
                "allowed": bool,
                "remaining": int,
                "reset_in": int,  # seconds until window resets
                "limit": int,
                "window": int,
                "dimension": str
            }
        """
        key = self._get_key(dimension, identifier, endpoint)
        now = time.time()
        
        # Get limit for this endpoint/dimension
        if window_override and limit_override:
            window = window_override
            limit = limit_override
        else:
            window, limit = self._get_limit(endpoint, dimension)
        
        window_start = now - window
        
        # Atomic sliding window operation (Lua script for atomicity)
        lua_script = """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local window_start = tonumber(ARGV[2])
            local limit = tonumber(ARGV[3])
            
            -- Remove old entries
            redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
            
            -- Count current entries
            local current = redis.call('ZCARD', key)
            
            if current >= limit then
                -- Get oldest timestamp for reset info
                local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
                return {0, current, oldest[2] or 0}
            end
            
            -- Add new request
            redis.call('ZADD', key, now, now)
            redis.call('EXPIRE', key, window + 5)
            
            return {1, current + 1, 0}
        """
        
        try:
            result = self.redis.eval(
                lua_script,
                1,
                key,
                str(now),
                str(window_start),
                str(limit)
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
                "key": key
            }
            
        except Exception as e:
            # Redis unavailable -> Fail-open (Section 10.23)
            # Log alert but allow request
            print(f"Rate limiter error: {e}")
            return {
                "allowed": True,
                "remaining": 999,
                "reset_in": 0,
                "limit": 999,
                "window": window,
                "dimension": dimension,
                "key": key,
                "error": str(e)
            }
    
    def get_distributed_attack_indicator(
        self,
        ip: str,
        endpoint: str,
        threshold: int = 100
    ) -> bool:
        """Deteksi distributed attack (10.000 IP masing-masing 100 request)
        Section 10.25 - Distributed Attack Mitigation
        """
        key = f"ratelimit:distributed:{endpoint}:{ip}"
        now = time.time()
        window_start = now - 60  # Last minute
        
        # Count unique IPs for this endpoint in last minute
        # Using HyperLogLog for memory efficiency
        self.redis.pfadd(key, ip)
        self.redis.expire(key, 120)
        
        unique_ips = self.redis.pfcount(key)
        
        return unique_ips > threshold
