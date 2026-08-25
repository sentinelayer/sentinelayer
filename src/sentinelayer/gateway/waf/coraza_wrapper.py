import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from urllib.parse import unquote

logger = logging.getLogger(__name__)

# Coba import Coraza
try:
    from coraza import Coraza, CorazaConfig
    CORAZA_AVAILABLE = True
    logger.info("✅ Coraza available")
except ImportError:
    try:
        from pycoraza import Coraza, CorazaConfig
        CORAZA_AVAILABLE = True
        logger.info("✅ PyCoraza available")
    except ImportError:
        CORAZA_AVAILABLE = False
        logger.warning("⚠️ Coraza not available, using fallback")

class WAFEngine:
    def __init__(self):
        self.rules = []
        self.coraza = None
        self.use_coraza = CORAZA_AVAILABLE
        
        if self.use_coraza:
            self.init_coraza()
        else:
            self.load_fallback_rules()
        
        logger.info(f"WAF initialized with {len(self.rules)} rules")
    
    def init_coraza(self):
        """Initialize Coraza with OWASP CRS"""
        try:
            config = CorazaConfig()
            config.DebugLevel = 0
            config.ErrorLog = "/dev/null"
            
            # CRS rules (sederhana)
            crs_rules = [
                # SQL Injection
                "SecRule ARGS \"(?i)(union\\s+select|select\\s+.*\\s+from|insert\\s+into|delete\\s+from|drop\\s+table|--|#|/\\*|\\*/)\" \"id:942100,phase:2,deny,status:403,msg:'SQL Injection Attack'\"",
                # XSS
                "SecRule ARGS \"(?i)(<script|</script>|javascript:|onerror=|onload=|onclick=)\" \"id:941100,phase:2,deny,status:403,msg:'XSS Attack'\"",
                # Path Traversal
                "SecRule ARGS \"(?i)(\\.\\./|\\.\\.\\\\|/etc/passwd)\" \"id:930100,phase:2,deny,status:403,msg:'Path Traversal Attack'\"",
                # Command Injection
                "SecRule ARGS \"(?i)(;|\\||&&|\\$\\(|`)\\s*(ls|pwd|cat|echo|wget|curl|nc|bash|sh)\" \"id:932100,phase:2,deny,status:403,msg:'Command Injection Attack'\"",
                # Admin paths
                "SecRule REQUEST_URI \"(/admin|/administrator|/wp-admin|/phpmyadmin|/dashboard)\" \"id:910100,phase:1,deny,status:403,msg:'Admin Path Access'\"",
                # SSRF
                "SecRule ARGS \"(169\\.254\\.169\\.254|metadata\\.google|127\\.0\\.0\\.1|192\\.168\\.|10\\.)\" \"id:931100,phase:2,deny,status:403,msg:'SSRF Attack'\"",
            ]
            
            self.coraza = Coraza(config)
            for rule in crs_rules:
                self.coraza.AddRule(rule)
            
            logger.info(f"✅ Coraza initialized with {len(crs_rules)} rules")
            
        except Exception as e:
            logger.error(f"Coraza init failed: {e}")
            self.use_coraza = False
            self.load_fallback_rules()
    
    def load_fallback_rules(self):
        """Fallback rules (regex-based)"""
        self.rules = [
            {
                "id": "SQLI-001",
                "name": "SQL Injection",
                "pattern": r"(?i)(union\s+select|select\s+.*\s+from|insert\s+into|delete\s+from|drop\s+table|--|\#)",
                "severity": "critical",
                "locations": ["query", "body"]
            },
            {
                "id": "XSS-001",
                "name": "XSS",
                "pattern": r"(?i)(<script|</script>|javascript:|onerror=|onload=|onclick=)",
                "severity": "high",
                "locations": ["query", "body"]
            },
            {
                "id": "PATH-001",
                "name": "Path Traversal",
                "pattern": r"(\.\./|\.\.\\|/etc/passwd|/etc/shadow)",
                "severity": "high",
                "locations": ["path", "query"]
            },
            {
                "id": "CMD-001",
                "name": "Command Injection",
                "pattern": r"(?i)(;|\||\&\&)\s*(ls|pwd|cat|echo|wget|curl|nc|bash|sh)",
                "severity": "critical",
                "locations": ["query", "body"]
            },
            {
                "id": "ADMIN-001",
                "name": "Admin Path",
                "pattern": r"(/admin|/administrator|/wp-admin|/phpmyadmin|/dashboard)",
                "severity": "medium",
                "locations": ["path"]
            },
            {
                "id": "SSRF-001",
                "name": "SSRF",
                "pattern": r"(169\.254\.169\.254|metadata\.google|127\.0\.0\.1|192\.168\.|10\.)",
                "severity": "critical",
                "locations": ["query", "body"]
            },
        ]
        logger.info(f"Loaded {len(self.rules)} fallback rules")
    
    def inspect_request(self, path: str, query: str, body: str, headers: Dict) -> Dict:
        violations = []
        
        if self.use_coraza and self.coraza:
            try:
                # Combine request data
                full_path = path
                if query:
                    full_path = f"{path}?{query}"
                
                # Transaction
                tx = self.coraza.NewTransaction()
                tx.ProcessConnection("127.0.0.1", 0, "127.0.0.1", 0)
                tx.ProcessURI(full_path, "GET", "HTTP/1.1")
                tx.ProcessRequestHeaders()
                if body:
                    tx.ProcessRequestBody(body)
                tx.ProcessLogging()
                
                # Check if blocked
                if tx.Interrupted:
                    inter = tx.Interruption
                    if inter and inter.Status == 403:
                        violations.append({
                            "rule_id": "CORAZA-001",
                            "name": f"Coraza block: {inter.RuleId}",
                            "severity": "high",
                            "location": "coraza",
                            "match": "Coraza rule triggered"
                        })
            except Exception as e:
                logger.error(f"Coraza inspection error: {e}")
                # Fallback ke regex
                violations.extend(self._inspect_fallback(path, query, body, headers))
        else:
            violations.extend(self._inspect_fallback(path, query, body, headers))
        
        blocked = len(violations) > 0
        return {
            "blocked": blocked,
            "violations": violations,
            "severity": "critical" if blocked else "low",
            "rules_triggered": [v.get("rule_id", "unknown") for v in violations]
        }
    
    def _inspect_fallback(self, path: str, query: str, body: str, headers: Dict) -> List[Dict]:
        violations = []
        decoded_path = unquote(path)
        decoded_query = unquote(query)
        decoded_body = unquote(body)
        
        for location, text in [("path", decoded_path), ("query", decoded_query), ("body", decoded_body)]:
            if not text:
                continue
            for rule in self.rules:
                if location not in rule.get("locations", []):
                    continue
                import re
                if re.search(rule["pattern"], text, re.IGNORECASE):
                    violations.append({
                        "rule_id": rule["id"],
                        "name": rule["name"],
                        "severity": rule.get("severity", "medium"),
                        "location": location,
                        "match": text[:100]
                    })
        
        return violations

_waf = None

def get_waf_engine() -> WAFEngine:
    global _waf
    if _waf is None:
        _waf = WAFEngine()
    return _waf
