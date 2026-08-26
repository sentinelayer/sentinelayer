import os
import time
import redis
from typing import Dict

class RedisSlidingWindowRateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True
        )
        self.window_size = 60
        self.max_requests = int(os.getenv("RATE_LIMIT", "60"))

    def allow_request(self, key: str) -> Dict:
        current = int(time.time())
        try:
            self.redis_client.zremrangebyscore(key, 0, current - self.window_size)
            count = self.redis_client.zcard(key)
            if count >= self.max_requests:
                return {"allowed": False, "remaining": 0, "reset": current + self.window_size}
            self.redis_client.zadd(key, {str(current): current})
            self.redis_client.expire(key, self.window_size)
            return {"allowed": True, "remaining": self.max_requests - count - 1, "reset": current + self.window_size}
        except redis.ConnectionError:
            return {"allowed": True, "remaining": self.max_requests, "reset": current + self.window_size}
