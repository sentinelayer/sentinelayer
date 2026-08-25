class RateLimitTuning:
    def __init__(self):
        self.endpoint_limits = {
            "GET /health": 1000,
            "POST /api/v1/auth/login": 5,
            "GET /api/v1/orders": 100,
            "POST /api/v1/orders": 50,
            "PUT /api/v1/orders": 30,
            "DELETE /api/v1/orders": 20,
            "GET /api/v1/risk": 20,
            "POST /api/v1/risk": 10,
        }
    
    def get_limit(self, endpoint: str, method: str) -> int:
        return self.endpoint_limits.get(f"{method} {endpoint}", 100)

_tuning = None

def get_rate_limit_tuning():
    global _tuning
    if _tuning is None:
        _tuning = RateLimitTuning()
    return _tuning
