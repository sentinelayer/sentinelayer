# SentinelLayer - Status Aktual (2026-08-25)

## Bug Fixes Done
- WAF middleware KeyError
- authorization.py import time
- rate_limit middleware dipasang
- gate engine evidence ID
- counterfactual threshold
- risk confidence independent
- KMS env required
- migration duplikat dihapus
- admin backdoor dihapus

## Yang Jalan
- JWT auth (env secret)
- BOLA/IDOR (tanpa admin bypass)
- Rate limiting (Redis + in-memory)
- WAF regex fallback (6 rules)
- Risk engine (per-request)
- Decision safety (kill switch)
- Key rotation (Redis)
- KMS (AES-256 GCM)
- Audit logging

## Belum
- Coraza+CRS (masih regex)
- RLS aktif production
- Control Plane endpoints
- Dashboard UI lengkap
- AML/Fraud/PII
- Grafana/Loki

## Status
- 38/38 tests passing
- Siap deploy
