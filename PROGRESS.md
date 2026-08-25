# SentinelLayer - Status Aktual

## Yang Sudah Jalan
- FastAPI skeleton + routing
- JWT authentication (env-based secret)
- BOLA/IDOR check
- Rate limiting (Redis + in-memory)
- Tenant isolation (query-level + RLS migration)
- WAF regex fallback (6 rules)
- Behavior baseline (Redis persistence)
- Risk engine (per-request scoring)
- Decision safety (kill switch)
- Control plane models
- Threat intel
- AI layer
- Evidence matrix
- Gate engine
- Key rotation (Redis persistence)
- Runtime provenance
- KMS + secrets integration
- Audit logging
- Backup manager
- CI workflow

## Belum
- Coraza + OWASP CRS (masih regex fallback)
- RLS Postgres aktif di production
- Control Plane endpoints
- Dashboard UI lengkap
- AML/Fraud/PII detection
- Grafana/Loki observability

## Status
- 38/38 tests passing
- Siap deploy
