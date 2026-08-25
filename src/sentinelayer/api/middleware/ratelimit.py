from fastapi import Request, HTTPException, status
from typing import Optional
import logging
from sentinelayer.gateway.ratelimit.sliding_window import SimpleRateLimiter

logger = logging.getLogger(__name__)

class RateLimitMiddleware:
    """Rate limiting middleware untuk FastAPI"""
    
    def __init__(self):
        self.limiter = SimpleRateLimiter()
        self.default_limit = 100
        self.default_window = 60
    
    async def __call__(
        self,
        request: Request,
        endpoint: str = "",
        limit: Optional[int] = None,
        window: Optional[int] = None
    ):
        """Apply rate limiting berdasarkan request context"""
        
        # Skip rate limiting for public/health endpoints
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json", "/"]:
            return
        
        # Get identifier (IP + User if authenticated)
        identifier = request.client.host if request.client else "unknown"
        
        # Add user ID if authenticated
        if hasattr(request.state, "user_id"):
            identifier = f"{identifier}:{request.state.user_id}"
        
        # Add tenant ID if available
        if hasattr(request.state, "tenant_id"):
            identifier = f"{identifier}:{request.state.tenant_id}"
        
        # Check rate limit
        result = self.limiter.is_allowed(
            dimension="ip",
            identifier=identifier,
            endpoint=endpoint or request.url.path,
            limit=limit or self.default_limit,
            window=window or self.default_window
        )
        
        if not result["allowed"]:
            logger.warning(f"Rate limit exceeded: {identifier} on {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {result['reset_in']} seconds"
            )
        
        # Add rate limit headers
        request.state.rate_limit_remaining = result["remaining"]
        request.state.rate_limit_reset = result["reset_in"]
        
        return result
