# SentinelLayer remediation evidence — 2026-10-02

Status: repository remediation verified locally; production acceptance remains open.

## Changes

- Centralize production detection across the API, KMS, signing, workers, behavior and risk services. Either `SL_ENV` or `ENVIRONMENT` set to `prod`/`production` activates production safeguards.
- Reject automatic schema creation in production before database side effects. Verify the manifest first; dispose the engine when the application exits, including exceptions.
- Accept consistent provenance enforcement values (`1`/`true`), require matching SHA-256 digests, and regenerate the source manifest.
- Prevent public registration from joining an existing tenant. Validate tenant identifiers and reject passwords exceeding bcrypt's 72-byte boundary. Reject inactive-account login and passwords exceeding the bcrypt boundary at login/admin user creation as well.
- Require JWT expiry and identity claims; require a persistent session identifier in production. Verify active, matching session owners; apply admin demotion immediately; reject API keys belonging to inactive/missing users.
- Validate WebSocket sessions against stored revocation, expiry and active ownership, including on incoming messages and before outgoing broadcasts. Idle sockets recheck every 30 seconds and close after invalidation.
- Prevent SPA fallback paths and symlinks from exposing files outside the dashboard directory.
- Require gateway JWT expiry. Use authenticated identity and the socket client address in rate-limit keys instead of attacker-controlled session/API-key/user headers and ephemeral ports.
- Correct relative backup checksum paths. Make actual restores fail on errors and execute in a single transaction.
- Validate launcher configuration before migration and wait for HTTP health/readiness instead of TCP acceptance alone.
- Run the complete local Python regression selection, Go tests/vet/build, dashboard build, live API smoke tests and a real PostgreSQL backup/restore round trip in CI. Make BOLA tests fail when setup fails instead of silently skipping.

## Verified locally

| Check | Evidence | Scope |
| --- | --- | --- |
| Python regressions | 127 passed; 13 integration cases excluded | In-process/unit, smoke and existing local load/DR adapter checks; not PostgreSQL or cloud chaos |
| Live API | 5 passed | Disposable SQLite-backed Uvicorn; positive owner access, cross-tenant denial/list isolation, auth/login/logout |
| Gateway | All Go package tests, `go vet ./...`, build passed | Includes JWT expiry, provenance and rate-limit identity regressions |
| Gateway E2E | Passed with real Redis 7.4 | Safe proxy, CRS body SQLi blocking, gzip body blocking, critical auth, body-size limit |
| Dashboard | Production build passed | Compilation; full interactive browser acceptance not performed |
| Integrity | Python compilation, Bash syntax, YAML parsing, source-manifest verification, `git diff --check` passed | Repository checks |

The local environment has no Docker/PostgreSQL server. GitHub CI for commit `5772e6938efcd45540c04d5ff8b68b27f48a5cfa` passed all five jobs: unit, gateway, gateway E2E, Docker image and security integration. Its PostgreSQL job passed migrations 0001–0025, five live API cases, one unprivileged RLS probe and the real backup/restore test. See https://github.com/sentinelayer/sentinelayer/actions/runs/37067052225 . CI for follow-up commit `214c0d2758c03043c91596be396c81bf41e64cae` also passed all five jobs, including the transaction-context and all-tenant-table policy checks: https://github.com/sentinelayer/sentinelayer/actions/runs/37067782594 . Its Trivy scans passed; Semgrep identified the newly added mutable setup-node tag. Pin that action to the resolved full commit SHA. Inspect all workflows for the final commit before counting the final security state as successful. The third revision passed Semgrep, both Trivy scans, E2E Security, SBOM, Operational Readiness and Security Gate, while Gitleaks flagged a dummy fixture value in the WebSocket test. Replace that hardcoded value with a runtime-generated random value; retain the detector and rerun security CI. No external production deployment was performed.

The initial security scans found six fixed-version findings in PyJWT 2.13.0 (one critical, five high). Update both installation declarations to 2.14.0, the fixed version reported by Trivy and the upstream security release. Existing HS256 authentication tests pass against the updated library; both Trivy workflows passed for commit `214c0d2`; the final security workflow must also pass.

Webhook delivery now resolves once and connects directly to validated numeric addresses. It disables environment proxies and automatic redirects, while preserving the original HTTPS hostname for SNI and certificate validation. Real local HTTP/TLS tests verify no second DNS lookup, correct Host, verified certificates, ignored hostile proxy settings and rejected redirects. The resolver is mocked only to route the test destination to the disposable local server.

Tenant sessions now restore transaction-local context whenever a new transaction starts, including after commit/rollback. Exact tenant IDs are preserved instead of silently rewritten. Remove the unused legacy RLS helper with its separate-connection/session-scoped settings and invalid policy SQL; schema policies are owned by Alembic migrations.

## Dependency audit expansion

Auditing the resolved Python dependency graph exposed findings not covered by the original direct-requirements/high-severity Trivy selection. Update FastAPI/Starlette, PyJWT, python-multipart, requests, pytest and pytest-asyncio; remove python-jose and Passlib because repository code has no imports or usage of either. This also removes unused ECDSA/ASN.1 dependencies, including an unfixed advisory. The updated resolved requirement graph reports **no known vulnerabilities** with pip-audit. This is scanner evidence for this date, not a guarantee against undisclosed vulnerabilities.

Final Python pins: FastAPI 0.142.2, Starlette 1.7.0, PyJWT 2.15.1, python-multipart 0.0.32, requests 2.34.2, pytest 9.1.1 and pytest-asyncio 1.4.0. Application regressions and the live API/gateway probes pass after the upgrades. See upstream compatibility/security notes: https://fastapi.tiangolo.com/release-notes/ and https://pyjwt.readthedocs.io/en/latest/changelog.html .

Auditing all JavaScript lockfiles including development dependencies also found vulnerable Vite/esbuild, React Router and Cloudflare tooling chains. Update Vite to the fixed 6.4 branch, React Router to 7.18.4+, compatible React plugin 4.7+, and Cloudflare tooling within its declared version ranges; regenerate both dashboard/workspace locks and the Cloudflare lock. Require all three npm audits and Cloudflare typechecking in CI alongside dashboard compilation. This changes dependency major versions; interactive dashboard routing/login acceptance on the deployment remains required.

## Open production gates

1. **Database privilege model and request coverage.** The existing CI API connection is a database superuser. Its API tests prove application filtering, not that production RLS protects every request. The unprivileged RLS test covers `legal_holds`; it does not establish all-table coverage or production role configuration. Use a dedicated non-owner/non-superuser runtime role and separate migration/bootstrap privileges; prove full request behavior under those roles. Passing transaction-context and schema-policy checks expand the CI evidence, but do not establish deployment role privileges.
2. **End-to-end policy and event behavior.** Gateway policy version is currently hardcoded; prove distribution and enforcement of signed control-plane policy updates. The WebSocket manager is process-local and broadcasts received client messages; durable server telemetry and multiworker delivery are not demonstrated.
3. **Deployment acceptance.** Prove the actual production image starts with managed keys, artifact digests, least-privilege database credentials, Redis, HTTPS/proxy configuration and HTTP readiness. Demonstrate rollback, observability and recovery using deployment-owned infrastructure. Gateway client addressing behind a reverse proxy needs an explicit trusted-proxy design.
4. **Recovery scope.** The new real restore test proves a small disposable database round trip and corruption rejection. It does not prove full application recovery, encrypted key recovery, production RTO/RPO or application-managed backup paths.

These are acceptance requirements, not completed claims. Repository tests passing alone do not establish overall production readiness.
