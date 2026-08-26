# Attack Trees

## Root: Compromise API Security

### Node 1: Bypass Authentication
- **1.1** Brute force JWT → Rate limit blocks
- **1.2** Steal JWT → TLS protects
- **1.3** Default credentials → Enforced in code

### Node 2: Bypass Authorization
- **2.1** BOLA/IDOR → Tenant middleware blocks
- **2.2** Role escalation → RBAC blocks
- **2.3** Parameter tampering → WAF blocks

### Node 3: Exploit API
- **3.1** SQL Injection → WAF regex blocks
- **3.2** XSS → WAF regex blocks
- **3.3** Command Injection → WAF regex blocks
- **3.4** SSRF → SSRF middleware blocks

### Node 4: Deny Service
- **4.1** Rate limit bypass → Redis sliding window
- **4.2** Resource exhaustion → Circuit breaker
