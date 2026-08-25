"""
WAF Middleware menggunakan Coraza + OWASP CRS
Section 10.8 - WAF Integration
"""

import json
import logging
from typing import Dict, Any, Optional
from fastapi import Request, Response, HTTPException, status

logger = logging.getLogger(__name__)

class CorazaWAF:
    """
    WAF wrapper untuk Coraza + OWASP CRS
    """
    
    def __init__(self):
        self.enabled = True
        self.rules = []
        self.load_default_rules()
        
    def load_default_rules(self):
        """Load default WAF rules (OWASP CRS)"""
        # Basic SQL Injection patterns
        self.rules.extend([
            {
                "id": "SQLI-001",
                "name": "SQL Injection Detection",
                "pattern": r"(?i)(union\s+select|select\s+.*\s+from|insert\s+into|delete\s+from|drop\s+table|--|;)",
                "action": "block",
                "severity": "high"
            },
            {
                "id": "XSS-001",
                "name": "XSS Detection",
                "pattern": r"(?i)(<script|alert\(|onerror=|onload=|javascript:|document\.cookie)",
                "action": "block",
                "severity": "high"
            },
            {
                "id": "PATH-001",
                "name": "Path Traversal Detection",
                "pattern": r"(\.\./|\.\.\\|/etc/passwd|/proc/self/environ)",
                "action": "block",
                "severity": "high"
            },
            {
                "id": "CMD-001",
                "name": "Command Injection Detection",
                "pattern": r"(?i)(;|\||&&|\$\()(ls|pwd|cat|echo|wget|curl|nc|bash|sh)",
                "action": "block",
                "severity": "critical"
            },
            {
                "id": "FILE-001",
                "name": "File Upload Detection",
                "pattern": r"(\.php|\.jsp|\.asp|\.exe|\.sh|\.pl|\.cgi)",
                "action": "block",
                "severity": "medium"
            },
        ])
        
        # Path-specific rules
        self.rules.extend([
            {
                "id": "ADMIN-001",
                "name": "Admin Path Protection",
                "pattern": r"/(admin|administrator|wp-admin|phpmyadmin|dashboard)",
                "action": "block",
                "severity": "high"
            },
            {
                "id": "SENSITIVE-001",
                "name": "Sensitive Data Protection",
                "pattern": r"/(\.env|\.git|\.aws|\.ssh|config\.json|secrets\.yml)",
                "action": "block",
                "severity": "critical"
            }
        ])
    
    async def inspect_request(self, request: Request) -> Dict[str, Any]:
        """
        Inspect request for WAF violations
        
        Returns:
            {
                "blocked": bool,
                "violations": list,
                "severity": str,
                "rules_triggered": list
            }
        """
        if not self.enabled:
            return {"blocked": False, "violations": []}
        
        violations = []
        severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        max_severity = "low"
        
        # Check path
        path = request.url.path
        if path:
            for rule in self.rules:
                if self._match_pattern(rule["pattern"], path):
                    violations.append({
                        "rule_id": rule["id"],
                        "name": rule["name"],
                        "match": path,
                        "severity": rule["severity"],
                        "location": "path"
                    })
                    if severity_levels.get(rule["severity"], 0) > severity_levels.get(max_severity, 0):
                        max_severity = rule["severity"]
        
        # Check query parameters
        for key, value in request.query_params.items():
            if self._is_suspicious(str(value)):
                violations.append({
                    "rule_id": "SQLI-001",
                    "name": "Suspicious query parameter",
                    "match": f"{key}={value}",
                    "severity": "high",
                    "location": "query"
                })
                max_severity = "high"
        
        # Check body (for POST/PUT)
        if request.method in ["POST", "PUT"]:
            try:
                body = await request.json()
                if body:
                    violations.extend(self._check_json_body(body))
            except:
                # Non-JSON body, check as string
                try:
                    body_bytes = await request.body()
                    body_str = body_bytes.decode('utf-8', errors='ignore')
                    if self._is_suspicious(body_str):
                        violations.append({
                            "rule_id": "SQLI-001",
                            "name": "Suspicious request body",
                            "match": body_str[:100],
                            "severity": "high",
                            "location": "body"
                        })
                        max_severity = "high"
                except:
                    pass
        
        # Check headers
        for key, value in request.headers.items():
            if key.lower() in ["user-agent", "referer", "x-forwarded-for"]:
                if self._is_suspicious(str(value)):
                    violations.append({
                        "rule_id": "HEADER-001",
                        "name": f"Suspicious {key} header",
                        "match": value,
                        "severity": "medium",
                        "location": "header"
                    })
                    max_severity = "medium"
        
        # Determine if blocked
        blocked = len(violations) > 0 and max_severity in ["high", "critical"]
        
        return {
            "blocked": blocked,
            "violations": violations,
            "severity": max_severity,
            "rules_triggered": [v["rule_id"] for v in violations]
        }
    
    def _match_pattern(self, pattern: str, text: str) -> bool:
        """Match regex pattern against text"""
        import re
        try:
            return bool(re.search(pattern, text, re.IGNORECASE))
        except:
            return False
    
    def _is_suspicious(self, text: str) -> bool:
        """Check if text contains suspicious patterns"""
        for rule in self.rules:
            if self._match_pattern(rule["pattern"], text):
                return True
        return False
    
    def _check_json_body(self, body: Any) -> list:
        """Recursively check JSON body for suspicious content"""
        violations = []
        if isinstance(body, dict):
            for key, value in body.items():
                if isinstance(value, str) and self._is_suspicious(value):
                    violations.append({
                        "rule_id": "SQLI-001",
                        "name": f"Suspicious value in {key}",
                        "match": value[:100],
                        "severity": "high",
                        "location": "body"
                    })
                elif isinstance(value, dict):
                    violations.extend(self._check_json_body(value))
                elif isinstance(value, list):
                    for item in value:
                        violations.extend(self._check_json_body(item))
        elif isinstance(body, list):
            for item in body:
                violations.extend(self._check_json_body(item))
        return violations
