from fastapi import Request
from fastapi.responses import JSONResponse
import re
import os

class WAFMiddleware:
    def __init__(self):
        self.rules = []
        self.load_rules()
    
    def load_rules(self):
        # SQL Injection patterns
        self.rules.append({
            "id": "SQLI-001",
            "pattern": r"(?i)(select|insert|update|delete|drop|union|exec|master|script|--|;|\b(OR|AND)\s+\d+\s*=\s*\d+)",
            "description": "SQL Injection"
        })
        # XSS patterns
        self.rules.append({
            "id": "XSS-001",
            "pattern": r"(?i)(<script|alert\(|onerror=|onclick=|onload=|javascript:|<iframe|document\.cookie)",
            "description": "XSS Attack"
        })
        # Path traversal
        self.rules.append({
            "id": "PT-001",
            "pattern": r"(\.\./|\.\.\\)",
            "description": "Path Traversal"
        })
        # Command injection
        self.rules.append({
            "id": "CMD-001",
            "pattern": r"(?i)(\||;|\&\&|`|\$\(|ping\s|wget\s|curl\s|nmap\s|python\s-c)",
            "description": "Command Injection"
        })
    
    def is_malicious(self, text: str) -> dict:
        if not text:
            return {"blocked": False}
        
        for rule in self.rules:
            if re.search(rule["pattern"], text):
                return {
                    "blocked": True,
                    "rule_id": rule["id"],
                    "description": rule["description"]
                }
        return {"blocked": False}
    
    async def process(self, request: Request, call_next):
        # Check query params
        for key, value in request.query_params.items():
            result = self.is_malicious(value)
            if result["blocked"]:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "WAF Blocked",
                        "rule": result["rule_id"],
                        "description": result["description"],
                        "parameter": key
                    }
                )
        
        # Check request body (only if JSON)
        try:
            body = await request.json()
            self._check_dict(body)
        except:
            pass
        
        return await call_next(request)
    
    def _check_dict(self, obj):
        if isinstance(obj, dict):
            for value in obj.values():
                self._check_dict(value)
        elif isinstance(obj, list):
            for item in obj:
                self._check_dict(item)
        elif isinstance(obj, str):
            result = self.is_malicious(obj)
            if result["blocked"]:
                raise Exception(f"Malicious content detected: {result['description']}")

waf_middleware = WAFMiddleware()
