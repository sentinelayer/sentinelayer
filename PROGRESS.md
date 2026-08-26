# SentinelLayer Progress

## Audit fix batch
- P0: applications/tenants/policies **tenant-scoped** (BOLA path closed in API)
- Removed dummy tests (test_dr_real assert True, weak bola/tenant stubs)
- Redis rate limiter score/member fix + fail-open on error
- Behavior EmitSignal logs + optional HTTP ingest
- docker-compose.yml valid (postgres, redis, risk, control-plane)
- KMS refuses missing key in production

## Still real gaps
- Policy model may lack tenant_id column → isolation via application join
- Integration tests need CP + DB up
- External Retainer unsigned
- Dashboard still thin UI over APIs
