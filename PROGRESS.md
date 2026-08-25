# SentinelLayer - Status Aktual

## Yang Sudah Jalan (di kode)
- FastAPI skeleton + routing (orders, behavior, risk, decision, controlplane, threatintel, ai, evidence, gate, keys, provenance)
- JWT authentication (HS256)
- BOLA/IDOR check (pake database)
- Rate limiting (Redis + in-memory fallback)
- Tenant isolation di query level (OrderRepository filter tenant_id)
- WAF regex fallback (6 rules)
- Behavior baseline (Redis persistence)
- Risk engine (per-request)
- Decision safety (kill switch)
- Control plane models (tenant/app/policy)
- Threat intel (local db mock)
- AI layer (mock)
- Evidence matrix
- Gate engine (running tests, not just collecting)
- Key rotation (24h + scheduler)
- Runtime provenance (fail-closed)
- Audit logging
- Backup manager
- AML monitor
- Fraud detector
- PII detection
- Data retention
- HA manager
- Webhook security

## Yang Belum / Kurang
- Coraza + OWASP CRS (hanya regex fallback)
- RLS Postgres (migration ada tapi perlu dipastikan jalan)
- Dashboard (frontend masih boilerplate)
- Full Control Plane (CRUD tenant/app/policy/incident)
- Sequence detection (basic)
- Signal correlation (basic)
- Counterfactual (basic)
- OWASP LLM Top 10 compliance
- MITRE ATLAS mapping
- Blast Radius Control
- Multi-region policy consistency
- Observability full stack (Grafana/Loki belum aktif)
- API versioning v2 (router belum diimplementasi)

## Status
- Tests: 38/38 passing (dengan TESTING=true)
- Deployment: Railway/Render siap
- Production readiness: masih perlu fix beberapa blocker
