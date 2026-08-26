# Threat Control Closure

| Threat | Control | Detection | Evidence |
|--------|---------|-----------|----------|
| SQL Injection | WAF regex | 403 response | WAF logs |
| XSS | WAF regex | 403 response | WAF logs |
| Command Injection | WAF regex | 403 response | WAF logs |
| SSRF | SSRF middleware | 403 response | SSRF logs |
| BOLA/IDOR | Tenant middleware | 403 response | Auth logs |
| Rate Limit | Redis sliding window | 429 response | Rate logs |
| JWT Theft | TLS + short expiry | Auth failure | Auth logs |
