# SentinelLayer - Status Aktual

## Yang Sudah Jalan
- FastAPI skeleton + routing (orders, behavior, risk, decision, controlplane, threatintel, ai, evidence, gate, keys, provenance)
- JWT authentication (PyJWT, HS256)
- BOLA/IDOR check (pake database)
- Rate limiting (Redis + in-memory fallback)
- Tenant isolation di query level (OrderRepository filter tenant_id)
- WAF regex fallback (6 rules)
- Behavior baseline (Redis persistence)
- Risk engine (per-request)
- Decision safety (kill switch)
- Control plane models (tenant/app/policy/incident - models only, no endpoints yet)
- Threat intel (local db mock)
- AI layer (mock)
- Evidence matrix
- Gate engine (running tests, not just collecting)
- Key rotation (24h + scheduler)
- Runtime provenance (fail-closed)
- RLS migration file (Postgres)
- Audit logging
- Backup manager
- CI workflow (Trivy, Semgrep, bandit)
- Frontend dashboard (basic CRUD UI)

## Belum / Kurang
- Coraza + OWASP CRS (hanya regex fallback)
- RLS Postgres aktif di production (migration ada tapi perlu dipastikan jalan)
- Dashboard UI lengkap (masih basic)
- Control Plane endpoints (/tenants, /applications, /policies, /incidents)
- Blast Radius Control
- Multi-region policy consistency
- OWASP LLM Top 10 compliance
- MITRE ATLAS mapping
- Observability full stack (Grafana/Loki belum aktif)
- API versioning v2 (router belum diimplementasi)
- AML monitoring (belum)
- Fraud detection (belum)
- PII detection (belum)
- Data retention (belum)
- HA manager (belum)
- Webhook security (belum)

## Status
- Tests: 38/38 passing (dengan TESTING=true)
- Deployment: Railway siap
- Production readiness: API functional, but beberapa security features masih partial
