from fastapi import Request, status
from fastapi.responses import JSONResponse
from sentinelayer.gateway.ssrf import validate_url

class SSRFMiddleware:
    async def __call__(self, request: Request):
        query_params = request.query_params
        for key in ["url", "redirect", "callback", "webhook", "endpoint", "target"]:
            if key in query_params:
                value = query_params[key]
                if value and not validate_url(value):
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"error": "SSRF protection triggered", "path": request.url.path}
                    )
        return None
