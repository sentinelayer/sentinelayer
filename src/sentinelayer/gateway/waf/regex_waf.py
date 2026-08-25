import re
import logging
from typing import Dict, List, Any
from urllib.parse import unquote

logger = logging.getLogger(__name__)

class WAFEngine:
    def __init__(self):
        self.rules = [
            {"id": "SQLI-001", "pattern": r"(?i)(union\s+select|select\s+.*\s+from|insert\s+into|delete\s+from|drop\s+table|--|\#)", "severity": "critical"},
            {"id": "XSS-001", "pattern": r"(?i)(<script|</script>|javascript:|onerror=|onload=|onclick=)", "severity": "high"},
            {"id": "PATH-001", "pattern": r"(\.\./|\.\.\\|/etc/passwd|/etc/shadow)", "severity": "high"},
            {"id": "CMD-001", "pattern": r"(?i)(;|\||\&\&)\s*(ls|pwd|cat|echo|wget|curl|nc|bash|sh)", "severity": "critical"},
            {"id": "ADMIN-001", "pattern": r"(/admin|/administrator|/wp-admin|/phpmyadmin|/dashboard)", "severity": "medium"},
            {"id": "SSRF-001", "pattern": r"(169\.254\.169\.254|metadata\.google|127\.0\.0\.1|192\.168\.|10\.)", "severity": "critical"},
        ]
        logger.info(f"WAF initialized with {len(self.rules)} regex rules (fallback mode)")
    
    def inspect_request(self, path: str, query: str, body: str, headers: Dict) -> Dict:
        violations = []
        decoded_path = unquote(path)
        decoded_query = unquote(query)
        decoded_body = unquote(body)
        
        for location, text in [("path", decoded_path), ("query", decoded_query), ("body", decoded_body)]:
            if not text:
                continue
            for rule in self.rules:
                if re.search(rule["pattern"], text, re.IGNORECASE):
                    violations.append({
                        "rule_id": rule["id"],
                        "severity": rule["severity"],
                        "location": location,
                        "match": text[:100]
                    })
        
        return {
            "blocked": len(violations) > 0,
            "violations": violations,
            "severity": "critical" if violations else "low",
            "rules_triggered": [v["rule_id"] for v in violations]
        }

_waf = None

def get_waf_engine():
    global _waf
    if _waf is None:
        _waf = WAFEngine()
    return _waf
