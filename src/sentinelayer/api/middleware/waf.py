from fastapi import Request, HTTPException, status
import logging
from sentinelayer.gateway.waf.coraza_wrapper import get_waf_engine

logger = logging.getLogger(__name__)

class WAFMiddleware:
    def __init__(self):
        self.waf = get_waf_engine()
        self.block_mode = True
        logger.info(f"WAF initialized with {len(self.waf.rules)} rules")
    
    async def __call__(self, request: Request):
        skip_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/", "/metrics"]
        if request.url.path in skip_paths:
            return
        
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""
        body = ""
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                body = body_bytes.decode('utf-8', errors='ignore')[:10000]
            except:
                pass
        headers = dict(request.headers)
        
        result = self.waf.inspect_request(path, query, body, headers)
        
        if result["violations"]:
            logger.warning(f"WAF violations: {len(result['violations'])} on {request.method} {request.url.path}")
            for v in result["violations"]:
                logger.warning(f"  - {v.get('rule_id', 'unknown')}: {v.get('severity', 'unknown')}")
        
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
        
        request.state.waf_violations = len(result["violations"])
        request.state.waf_severity = result["severity"]
        return result
