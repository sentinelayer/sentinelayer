import os
import time
import redis
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True
        )
        self.window_size = 60
        self.max_requests = int(os.getenv("RATE_LIMIT", "60"))

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/", "/docs", "/openapi.json", "/health", "/health/readiness"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}"
        current = int(time.time())

        try:
            self.redis_client.zremrangebyscore(key, 0, current - self.window_size)
            count = self.redis_client.zcard(key)

            if count >= self.max_requests:
                return JSONResponse(status_code=429, content={"error": "Rate limit exceeded"})

            self.redis_client.zadd(key, {str(current): current})
            self.redis_client.expire(key, self.window_size)
        except redis.ConnectionError:
            pass

        return await call_next(request)
