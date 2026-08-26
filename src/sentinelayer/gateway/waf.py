import re
from fastapi import Request
from fastapi.responses import JSONResponse

class WAFMiddleware:
    def __init__(self):
        self.rules = []
        self.load_rules()

    def load_rules(self):
        self.rules.append({"id": "SQLI-001", "pattern": r"(?i)(select|insert|update|delete|drop|union|exec|master|script|--|;|\b(OR|AND)\s+\d+\s*=\s*\d+)", "description": "SQL Injection"})
        self.rules.append({"id": "XSS-001", "pattern": r"(?i)(<script|alert\(|onerror=|onclick=|onload=|javascript:|<iframe|document\.cookie)", "description": "XSS Attack"})
        self.rules.append({"id": "PT-001", "pattern": r"(\.\./|\.\.\\)", "description": "Path Traversal"})
        self.rules.append({"id": "CMD-001", "pattern": r"(?i)(\||;|\&\&|`|\$\(|ping\s|wget\s|curl\s|nmap\s|python\s-c)", "description": "Command Injection"})

    def is_malicious(self, text: str) -> dict:
        if not text:
            return {"blocked": False, "rule_id": None, "description": None}
        for rule in self.rules:
            if re.search(rule["pattern"], text):
                return {"blocked": True, "rule_id": rule["id"], "description": rule["description"]}
        return {"blocked": False, "rule_id": None, "description": None}

    def _check_dict(self, obj):
        if isinstance(obj, dict):
            for value in obj.values():
                result = self._check_dict(value)
                if result and result.get("blocked"):
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = self._check_dict(item)
                if result and result.get("blocked"):
                    return result
        elif isinstance(obj, str):
            return self.is_malicious(obj)
        return {"blocked": False, "rule_id": None, "description": None}

    async def process(self, request: Request, call_next):
        for key, value in request.query_params.items():
            result = self.is_malicious(value)
            if result["blocked"]:
                from src.sentinelayer.api.metrics import increment_waf_block
                increment_waf_block()
                return JSONResponse(status_code=403, content={"error": "WAF Blocked", "rule": result["rule_id"]})

        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
                result = self._check_dict(body)
                if result and result.get("blocked"):
                    from src.sentinelayer.api.metrics import increment_waf_block
                    increment_waf_block()
                    return JSONResponse(status_code=403, content={"error": "WAF Blocked", "rule": result["rule_id"]})
            except:
                pass

        return await call_next(request)

waf_middleware = WAFMiddleware()
