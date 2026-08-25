import re
import logging
from typing import Dict, List
from dataclasses import dataclass
from urllib.parse import unquote

logger = logging.getLogger(__name__)

@dataclass
class WAFRule:
    id: str
    name: str
    pattern: str
    action: str
    severity: str
    locations: List[str]

class WAFEngine:
    def __init__(self):
        self.rules = []
        self.load_default_rules()
        logger.info(f"Loaded {len(self.rules)} WAF rules")
    
    def load_default_rules(self):
        # SQL Injection
        self.rules.append(WAFRule(
            id="SQLI-001",
            name="SQL Injection",
            pattern=r"(?i)(union\s+select|select\s+.*\s+from|insert\s+into|delete\s+from|drop\s+table|--|\#)",
            action="block",
            severity="critical",
            locations=["query", "body"]
        ))
        
        # XSS
        self.rules.append(WAFRule(
            id="XSS-001",
            name="XSS",
            pattern=r"(?i)(<script|</script>|javascript:|onerror=|onload=|onclick=)",
            action="block",
            severity="high",
            locations=["query", "body"]
        ))
        
        # Path Traversal
        self.rules.append(WAFRule(
            id="PATH-001",
            name="Path Traversal",
            pattern=r"(\.\./|\.\.\\|/etc/passwd|/etc/shadow)",
            action="block",
            severity="high",
            locations=["path", "query"]
        ))
        
        # Command Injection
        self.rules.append(WAFRule(
            id="CMD-001",
            name="Command Injection",
            pattern=r"(?i)(;|\||\&\&)\s*(ls|pwd|cat|echo|wget|curl|nc|bash|sh)",
            action="block",
            severity="critical",
            locations=["query", "body"]
        ))
        
        # Admin Paths
        self.rules.append(WAFRule(
            id="ADMIN-001",
            name="Admin Path",
            pattern=r"(/admin|/administrator|/wp-admin|/phpmyadmin|/dashboard)",
            action="block",
            severity="medium",
            locations=["path"]
        ))
        
        # SSRF
        self.rules.append(WAFRule(
            id="SSRF-001",
            name="SSRF",
            pattern=r"(169\.254\.169\.254|metadata\.google|127\.0\.0\.1|192\.168\.|10\.)",
            action="block",
            severity="critical",
            locations=["query", "body"]
        ))
    
    def inspect_request(self, path: str, query: str, body: str, headers: Dict) -> Dict:
        violations = []
        
        decoded_path = unquote(path)
        decoded_query = unquote(query)
        decoded_body = unquote(body)
        
        for location, text in [("path", decoded_path), ("query", decoded_query), ("body", decoded_body)]:
            if not text:
                continue
            for rule in self.rules:
                if location not in rule.locations:
                    continue
                if re.search(rule.pattern, text, re.IGNORECASE):
                    violations.append({
                        "rule_id": rule.id,
                        "name": rule.name,
                        "severity": rule.severity,
                        "location": location,
                        "match": text[:100]
                    })
        
        blocked = len(violations) > 0
        
        return {
            "blocked": blocked,
            "violations": violations,
            "severity": "critical" if blocked else "low",
            "rules_triggered": [v["rule_id"] for v in violations]
        }

_waf = None

def get_waf_engine():
    global _waf
    if _waf is None:
        _waf = WAFEngine()
    return _waf
