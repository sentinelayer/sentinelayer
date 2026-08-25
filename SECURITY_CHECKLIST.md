# SentinelLayer Security Checklist

## Done
- [x] JWT Authentication (PyJWT, HS256)
- [x] BOLA/IDOR Protection
- [x] Rate Limiting (Redis + in-memory fallback)
- [x] Tenant Isolation (query-level + RLS migration)
- [x] WAF (regex fallback, 6 rules)
- [x] Risk Engine (per-request scoring)
- [x] Decision Safety (kill switch)
- [x] Key Rotation (24h, Redis persistence)
- [x] Runtime Provenance (fail-closed)
- [x] Audit Logging
- [x] Backup Manager

## Partial / In Progress
- [ ] WAF Coraza+CRS (currently regex fallback)
- [ ] RLS Postgres active in production
- [ ] Control Plane endpoints (/tenants, /applications, /policies)
- [ ] Dashboard UI complete

## Planned
- [ ] KMS integration with key_rotation
- [ ] AML/Fraud/PII detection
- [ ] Grafana/Loki observability
