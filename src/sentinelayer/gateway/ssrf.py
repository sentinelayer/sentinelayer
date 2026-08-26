from fastapi import Request, Response
from fastapi.responses import JSONResponse
import ipaddress
import re

class SSRFMiddleware:
    def __init__(self):
        self.blocked_ips = [
            "127.0.0.0/8",
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16",
            "169.254.0.0/16",
            "0.0.0.0/8",
            "224.0.0.0/4",
            "240.0.0.0/4"
        ]
        self.blocked_domains = [
            "localhost",
            "metadata.google.internal",
            "169.254.169.254"
        ]
    
    def is_blocked_url(self, url: str) -> bool:
        # Check IP addresses
        try:
            ip = ipaddress.ip_address(url.split("/")[0])
            for blocked in self.blocked_ips:
                if ip in ipaddress.ip_network(blocked):
                    return True
        except ValueError:
            pass
        
        # Check domains
        for domain in self.blocked_domains:
            if domain in url.lower():
                return True
        
        return False
    
    async def process(self, request: Request, call_next):
        # Check for URL parameters that might be SSRF
        for key, value in request.query_params.items():
            if "url" in key.lower() or "uri" in key.lower() or "path" in key.lower():
                if self.is_blocked_url(value):
                    return JSONResponse(
                        status_code=403,
                        content={"error": "SSRF attempt blocked"}
                    )
        
        return await call_next(request)

ssrf_middleware = SSRFMiddleware()
