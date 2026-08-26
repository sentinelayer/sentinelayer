# SentinelLayer Progress

## This batch
- Gateway service in docker-compose (Go 1.25 Dockerfile)
- Postgres RLS policies (§9.2) + migration 0004 + session SET app.tenant_id
- Applications/policies/incidents use db_with_tenant
- Offboarding API soft/hard with before/after hash (§9.19)
- Dashboard: login/register, applications, policies, incidents, overview

## Verified previously
- Live tenant isolation PASSED
- Risk engine + behavior + blast radius unit tests PASSED

## Still external / non-code
- External Retainer signature
- Full MFA device enrollment productization
- Production cosign/SBOM pipeline attestation
- Full adversarial matrix beyond BOLA API test
