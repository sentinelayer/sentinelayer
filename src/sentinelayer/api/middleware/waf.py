from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from sentinelayer.gateway.waf.coraza_wrapper import CorazaWAF

logger = logging.getLogger(__name__)

class WAFMiddleware:
    """WAF Middleware untuk FastAPI"""
    
    def __init__(self):
        self.waf = CorazaWAF()
    
    async def __call__(self, request: Request):
        """Apply WAF inspection to request"""
        
        # Skip WAF for health/docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json", "/"]:
            return
        
        # Inspect request
        result = await self.waf.inspect_request(request)
        
        # Log violations
        if result["violations"]:
            logger.warning(
                f"WAF violations detected: {len(result['violations'])} "
                f"(severity: {result['severity']})"
            )
            for v in result["violations"]:
                logger.warning(f"  - {v['rule_id']}: {v['name']} ({v['severity']})")
        
        # Block if necessary
        if result["blocked"]:
            logger.error(f"WAF BLOCKED request: {request.method} {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Request blocked by WAF",
                    "violations": result["violations"],
                    "severity": result["severity"]
                }
            )
        
        # Add WAF headers for visibility
        request.state.waf_violations = len(result["violations"])
        request.state.waf_severity = result["severity"]
        
        return result
