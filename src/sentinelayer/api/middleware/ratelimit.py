from fastapi import Request, HTTPException, status
from typing import Optional
import logging
import os

from sentinelayer.gateway.ratelimit.sliding_window import (
    RedisSlidingWindowRateLimiter,
    SimpleRateLimiter
)

logger = logging.getLogger(__name__)

# Use Redis if available, fallback to simple
try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    limiter = RedisSlidingWindowRateLimiter(redis_url)
    logger.info("Using Redis rate limiter")
except:
    limiter = SimpleRateLimiter()
    logger.warning("Redis not available, using simple rate limiter")

class RateLimitMiddleware:
    def __init__(self):
        self.limiter = limiter
        self.default_limit = 100
        self.default_window = 60
    
    async def __call__(
        self,
        request: Request,
        endpoint: str = "",
        limit: Optional[int] = None,
        window: Optional[int] = None
    ):
        # Skip rate limiting for health/docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json", "/", "/metrics"]:
            return
        
        # Get identifier
        identifier = request.client.host if request.client else "unknown"
        
        if hasattr(request.state, "user_id"):
            identifier = f"{identifier}:{request.state.user_id}"
        
        if hasattr(request.state, "tenant_id"):
            identifier = f"{identifier}:{request.state.tenant_id}"
        
        # Endpoint-specific limits
        endpoint_limits = {
            "/api/v1/auth/login": (5, 60),
            "/api/v1/orders/": (100, 60),
        }
        
        path = request.url.path
        method = request.method
        
        if path in endpoint_limits:
            limit, window = endpoint_limits[path]
        
        # Check rate limit - pake parameter yang bener
        result = self.limiter.is_allowed(
            dimension="ip",
            identifier=identifier,
            endpoint=path,
            limit=limit,      # ← pake limit, bukan limit_override
            window=window     # ← pake window, bukan window_override
        )
        
        if not result.get("allowed", False):
            logger.warning(f"Rate limit exceeded: {identifier} on {path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {result.get('reset_in', 60)} seconds"
            )
        
        request.state.rate_limit_remaining = result.get("remaining", 0)
        request.state.rate_limit_reset = result.get("reset_in", 60)
        
        return result
