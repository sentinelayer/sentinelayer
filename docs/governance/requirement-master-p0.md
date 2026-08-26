# Requirement Master List — P0 (Production Blockers)

Status: NOT_STARTED until GateEngine registers and evaluates them.

| Requirement ID | Title | Owner | Gate | Criticality |
|----------------|-------|-------|------|-------------|
| SL-SEC-AUTH-001 | JWT / API-key authentication on all protected endpoints | Founder | MVP | P0 |
| SL-SEC-AUTHZ-001 | Object-level authorization (BOLA/IDOR) | Founder | MVP | P0 |
| SL-SEC-TENANT-001 | Tenant isolation adversarial matrix (all paths) | Founder | MVP | P0 |
| SL-SEC-SECRET-001 | Secrets never in plaintext logs or AI context | Founder | MVP | P0 |
| SL-SEC-ENC-001 | TLS 1.3 in transit + AES-256 at rest | Founder | MVP | P0 |
| SL-SEC-WAF-001 | Coraza + OWASP CRS on data plane | Founder | MVP | P0 |
| SL-SEC-SSRF-001 | SSRF protection (private IP, metadata, DNS rebinding) | Founder | MVP | P0 |
| SL-SEC-SMUGGLING-001 | HTTP desync / request smuggling defenses | Founder | MVP | P0 |
| SL-SEC-PROV-001 | Runtime provenance verification at startup | Founder | MVP | P0 |
| SL-SEC-POLICY-001 | Policy signing key hierarchy + automatic 24h rotation | Founder | MVP | P0 |
| SL-SEC-FAIL-001 | Fail-open / fail-closed decision matrix enforced | Founder | MVP | P0 |
| SL-SEC-RL-001 | Abuse-economics rate limiting (multi-dimension) | Founder | MVP | P0 |

These IDs are the only ones that may block Production Gate.
