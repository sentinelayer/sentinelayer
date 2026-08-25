from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging
import json
from sentinelayer.gateway.waf.coraza_wrapper import get_waf_engine

logger = logging.getLogger(__name__)

class WAFMiddleware:
    """WAF Middleware untuk FastAPI"""
    
    def __init__(self):
        self.waf = get_waf_engine()
        self.block_mode = True  # Set to False for monitor-only mode
        logger.info(f"WAF initialized with {len(self.waf.rules)} rules")
    
    async def __call__(self, request: Request):
        """Apply WAF inspection to request"""
        
        # Skip WAF untuk public endpoints
        skip_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/", "/metrics"]
        if request.url.path in skip_paths:
            return
        
        # Get request data
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""
        
        # Get body (for POST/PUT)
        body = ""
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                body = body_bytes.decode('utf-8', errors='ignore')[:10000]
            except Exception as e:
                pass
        
        # Get headers
        headers = dict(request.headers)
        
        # Inspect request
        result = self.waf.inspect_request(path, query, body, headers)
        
        # Log violations
        if result["violations"]:
            logger.warning(
                f"WAF violations: {len(result['violations'])} "
                f"(severity: {result['severity']}) on {request.method} {request.url.path}"
            )
            for v in result["violations"][:3]:
                logger.warning(f"  - {v['rule_id']}: {v['name']} ({v['severity']})")
        
        # Block if necessary
        if self.block_mode and result["blocked"]:
            logger.error(f"WAF BLOCKED: {request.method} {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Request blocked by WAF",
                    "violations": result["violations"][:5],
                    "severity": result["severity"]
                }
            )
        
        # Add WAF headers
        request.state.waf_violations = len(result["violations"])
        request.state.waf_severity = result["severity"]
        
        return result
