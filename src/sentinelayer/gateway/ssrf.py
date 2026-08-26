from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import ipaddress
import socket

class SSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.blocked_ips = [
            "127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
            "169.254.0.0/16", "0.0.0.0/8", "224.0.0.0/4", "240.0.0.0/4",
            "::1", "fc00::/7", "fe80::/10"
        ]
        self.blocked_domains = ["localhost", "metadata.google.internal", "169.254.169.254"]

    def is_blocked(self, url: str) -> bool:
        hostname = url.split("/")[0].split(":")[0]
        try:
            ip = socket.gethostbyname(hostname)
            for blocked in self.blocked_ips:
                if ipaddress.ip_address(ip) in ipaddress.ip_network(blocked):
                    return True
        except:
            pass

        for domain in self.blocked_domains:
            if domain in url.lower():
                return True

        return False

    async def dispatch(self, request: Request, call_next):
        for key, value in request.query_params.items():
            if any(x in key.lower() for x in ["url", "uri", "path", "redirect"]):
                if self.is_blocked(value):
                    return JSONResponse(status_code=403, content={"error": "SSRF attempt blocked"})
        return await call_next(request)
