# SentinelLayer remediation evidence — 2026-10-02

Status: repository remediation verified locally; production acceptance remains open.

## Changes

- Centralize production detection across the API, KMS, signing, workers, behavior and risk services. Either `SL_ENV` or `ENVIRONMENT` set to `prod`/`production` activates production safeguards.
- Reject automatic schema creation in production before database side effects. Verify the manifest first; dispose the engine when the application exits, including exceptions.
- Accept consistent provenance enforcement values (`1`/`true`), require matching SHA-256 digests, and regenerate the source manifest.
- Prevent public registration from joining an existing tenant. Validate tenant identifiers and reject passwords exceeding bcrypt's 72-byte boundary. Reject inactive-account login.
- Require JWT expiry and identity claims; require a persistent session identifier in production. Verify active, matching session owners; apply admin demotion immediately; reject API keys belonging to inactive/missing users.
- Validate WebSocket sessions against stored revocation, expiry and active ownership, including on incoming messages. This does not actively close an idle socket at revocation time.
- Prevent SPA fallback paths and symlinks from exposing files outside the dashboard directory.
- Require gateway JWT expiry. Use authenticated identity and the socket client address in rate-limit keys instead of attacker-controlled session/API-key/user headers and ephemeral ports.
- Correct relative backup checksum paths. Make actual restores fail on errors and execute in a single transaction.
- Validate launcher configuration before migration and wait for HTTP health/readiness instead of TCP acceptance alone.
- Run the complete local Python regression selection, Go tests/vet/build, dashboard build, live API smoke tests and a real PostgreSQL backup/restore round trip in CI. Make BOLA tests fail when setup fails instead of silently skipping.

## Verified locally

| Check | Evidence | Scope |
| --- | --- | --- |
| Python regressions | 117 passed; 12 integration cases excluded after adding the restore test | In-process/unit, smoke and existing local load/DR adapter checks; not PostgreSQL or cloud chaos |
| Live API | 5 passed | Disposable SQLite-backed Uvicorn; positive owner access, cross-tenant denial/list isolation, auth/login/logout |
| Gateway | All Go package tests, `go vet ./...`, build passed | Includes JWT expiry, provenance and rate-limit identity regressions |
| Gateway E2E | Passed with real Redis 7.4 | Safe proxy, CRS body SQLi blocking, gzip body blocking, critical auth, body-size limit |
| Dashboard | Production build passed | Compilation; full interactive browser acceptance not performed |
| Integrity | Python compilation, Bash syntax, YAML parsing, source-manifest verification, `git diff --check` passed | Repository checks |

The local environment has no Docker/PostgreSQL server. The GitHub `security-integration` job exercises PostgreSQL migrations, API isolation, an unprivileged RLS probe and the real backup/restore test. Check the workflow for the exact commit before treating those as successful evidence. No external production deployment was performed.

## Open production gates

1. **Database privilege model and RLS coverage.** The existing CI API connection is a database superuser. Its API tests prove application filtering, not that production RLS protects every request. The unprivileged RLS test covers `legal_holds`; it does not establish all-table coverage or production role configuration. Use a dedicated non-owner/non-superuser runtime role and separate migration/bootstrap privileges; prove tenant context survives the complete transaction lifecycle. The legacy `infrastructure/db/rls.py` helper is not the active session path and needs removal or reconciliation before relying on it.
2. **Webhook delivery DNS pinning.** Resolving and checking a hostname before an opener resolves it again leaves a rebinding window. Delivery needs validated-address pinning with hostname/TLS preservation and corresponding network tests.
3. **End-to-end policy and event behavior.** Gateway policy version is currently hardcoded; prove distribution and enforcement of signed control-plane policy updates. The WebSocket manager is process-local and broadcasts received client messages; durable server telemetry and multiworker delivery are not demonstrated.
4. **Deployment acceptance.** Prove the actual production image starts with managed keys, artifact digests, least-privilege database credentials, Redis, HTTPS/proxy configuration and HTTP readiness. Demonstrate rollback, observability and recovery using deployment-owned infrastructure. Gateway client addressing behind a reverse proxy needs an explicit trusted-proxy design.
5. **Recovery scope.** The new real restore test proves a small disposable database round trip and corruption rejection. It does not prove full application recovery, encrypted key recovery, production RTO/RPO or application-managed backup paths.

These are acceptance requirements, not completed claims. Repository tests passing alone do not establish overall production readiness.
