# SentinelLayer Progress

## Code complete (this cycle)
- [x] Gateway full pipeline (Coraza → auth → rate → risk → decision → upstream)
- [x] Redis env (REDIS_ADDR / REDIS_URL)
- [x] events_ws websocket
- [x] MFA enrollment (setup / verify / disable / login) + smoke passed
- [x] CI: unit, gateway build, security-integration (BOLA + tenant matrix)
- [x] Release: cosign keyless + SBOM artifacts
- [x] Dashboard react-router + Layout navigation
- [x] Threat-intel static feed API
- [x] AI explain off-path API (local, non-blocking)
- [x] Provenance helper + docker-compose.prod.yml profile
- [x] Alembic 0005 MFA columns

## Remaining (cannot finish by code alone)
- [ ] GitHub Actions green confirmation on origin (human check)
- [ ] External Retainer contract + dual-control access
- [ ] Real HA multi-AZ deployment + DR drill evidence
- [ ] Pilot: 3 customers, success metrics, legal
- [ ] Enterprise SSO / SCIM
- [ ] Commercial GA (pricing, support SLA, compliance pack)

## Estimated
- Technical MVP path: \~40–45%
- Overall blueprint 0→100: \~30–35%
