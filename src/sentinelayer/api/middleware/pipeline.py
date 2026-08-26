from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.sentinelayer.behavior.engine import behavior_engine
from src.sentinelayer.risk.engine import risk_engine
from src.sentinelayer.decision.safemode import safe_mode

class SecurityPipelineMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/", "/docs", "/openapi.json", "/health", "/health/readiness", "/api/v1/auth/login", "/api/v1/auth/register"]:
            return await call_next(request)

        user_id = getattr(request.state, "user_id", "anonymous")
        tenant_id = getattr(request.state, "tenant_id", None)

        context = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "ip": request.client.host if request.client else "unknown",
            "path": request.url.path,
            "method": request.method
        }

        behavior_engine.track(context)

        risk_result = risk_engine.calculate(context)
        decision = safe_mode.process_decision({"action": risk_result["action"]})

        if decision["blocked"]:
            return JSONResponse(status_code=403, content={
                "error": "Request blocked by security policy",
                "risk_score": risk_result["score"],
                "action": decision["action"],
                "reason": decision.get("reason", "Security policy violation")
            })

        response = await call_next(request)

        return response
