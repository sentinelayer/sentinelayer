# SentinelLayer remediation evidence — 2026-10-02

Status: repository remediation verified locally and in GitHub CI; production acceptance remains open.

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
| Cloudflare | Typecheck passed | Compilation; no deployment performed |
| Dashboard | Production build passed | Compilation; full interactive browser acceptance not performed |
| Integrity | Python compilation, Bash syntax, YAML parsing, source-manifest verification, `git diff --check` passed | Repository checks |

## GitHub verification

Code commit: [`068002a1413b736e0ed39d4e05cbb590cc73d7be`](https://github.com/sentinelayer/sentinelayer/commit/068002a1413b736e0ed39d4e05cbb590cc73d7be).

- [CI](https://github.com/sentinelayer/sentinelayer/actions/runs/37069212959): all six jobs passed — Python regressions/dashboard build, Go tests/vet/build, gateway E2E, Docker image, PostgreSQL security integration, and Cloudflare typechecking.
- [Security](https://github.com/sentinelayer/sentinelayer/actions/runs/37069212914): all five jobs passed — Semgrep, Gitleaks, Trivy, resolved Python dependencies, and all JavaScript lockfiles including development dependencies.
- [Trivy](https://github.com/sentinelayer/sentinelayer/actions/runs/37069212863): passed.

PostgreSQL evidence includes migrations 0001–0025, five live API cases, the unprivileged legal-holds isolation probe, transaction-context survival after commit/rollback, policies on every modeled tenant table, and a real pg_dump/pg_restore round trip with corruption rejection.

The local environment has no Docker/PostgreSQL server; those results are from GitHub Actions. No external production deployment was performed.

Webhook delivery now resolves once and connects directly to validated numeric addresses. It disables environment proxies and automatic redirects, while preserving the original HTTPS hostname for SNI and certificate validation. Real local HTTP/TLS tests verify no second DNS lookup, correct Host, verified certificates, ignored hostile proxy settings and rejected redirects. The resolver is mocked only to route the test destination to the disposable local server.

Tenant sessions now restore transaction-local context whenever a new transaction starts, including after commit/rollback. Exact tenant IDs are preserved instead of silently rewritten. The unused legacy RLS helper was removed because it used separate connections, session-scoped settings and invalid policy SQL. Alembic migrations own schema policies.

## Dependency audit expansion

Auditing the resolved Python dependency graph exposed findings not covered by the original direct-requirements/high-severity Trivy selection. FastAPI/Starlette, PyJWT, python-multipart, requests, pytest and pytest-asyncio were updated. Unused python-jose and Passlib were removed; repository code has no imports or usage of either. This also removes unused ECDSA/ASN.1 dependencies, including an unfixed advisory. The updated resolved requirement graph reports **no known vulnerabilities** with pip-audit. This is scanner evidence for this date, not a guarantee against undisclosed vulnerabilities.

Final Python pins: FastAPI 0.142.2, Starlette 1.7.0, PyJWT 2.15.1, python-multipart 0.0.32, requests 2.34.2, pytest 9.1.1 and pytest-asyncio 1.4.0. Application regressions and the live API/gateway probes pass after the upgrades. See upstream compatibility/security notes: https://fastapi.tiangolo.com/release-notes/ and https://pyjwt.readthedocs.io/en/latest/changelog.html .

Auditing all JavaScript lockfiles including development dependencies also found vulnerable Vite/esbuild, React Router and Cloudflare tooling chains. Vite was updated to 6.4.3, React Router to 7.18.4+, the React plugin to 4.7+, and Cloudflare tooling within its declared version ranges. All three locks were regenerated and report zero findings in npm audit, including development dependencies. CI now requires those audits and Cloudflare typechecking alongside dashboard compilation. This changes dependency major versions; interactive dashboard routing/login acceptance on the deployment remains required.

## Open production gates

1. **Deployment database roles.** Repository provisioning and startup validation now separate app/auth/worker roles from migration ownership, reject elevated/shared identities and protect `tenants` with RLS. Real PostgreSQL CI proves unfiltered tenant scoping, privilege denials, five API probes under restricted production credentials and the worker one-shot. Configure and verify those roles on the actual deployment; CI does not prove deployed credentials. See [database roles](database-roles.md).
2. **Policy fleet rollout and durable events.** Optional single-tenant signed runtime policy now verifies pinned Ed25519 keys, identity/version/expiry and applies validated gateway rules with actual version provenance. Python-to-Go E2E covers the real API export and enforcement; Go tests cover expiry/fallback/rollback. Multi-tenant routing, fleet acknowledgement and a persistent version floor remain open. The WebSocket manager remains process-local; durable server telemetry and multiworker delivery are not demonstrated. See [runtime policy](gateway-runtime-policy.md).
3. **Deployment acceptance.** Prove the actual production image starts with managed keys, artifact digests, least-privilege database credentials, Redis, HTTPS/proxy configuration and HTTP readiness. Demonstrate rollback, observability and recovery using deployment-owned infrastructure. Gateway client addressing behind a reverse proxy needs an explicit trusted-proxy design.
4. **Recovery scope.** The new real restore test proves a small disposable database round trip and corruption rejection. It does not prove full application recovery, encrypted key recovery, production RTO/RPO or application-managed backup paths.

These are acceptance requirements, not completed claims. Repository tests passing alone do not establish overall production readiness.

## Restricted database and signed-policy follow-up

Database-role implementation commit: [`879781a7910b7e18f105551308220a7f6b0e063f`](https://github.com/sentinelayer/sentinelayer/commit/879781a7910b7e18f105551308220a7f6b0e063f). All six CI jobs passed, including PostgreSQL restricted-production runtime proof. Its Security workflow flagged ten safe psycopg2 DDL compositions as SQLAlchemy concatenation. The follow-up uses a closed privilege-keyword map and narrowly annotates only Identifier/Literal-composed DDL calls; the scanner remains enabled.

Follow-up local checks: 131 Python regressions passed (14 integration cases excluded), Go package tests and policy/gateway race tests passed, vet/build passed. The real Redis signed-policy E2E passed, including live adoption of a higher policy version without restarting the gateway. Production telemetry durability, fleet policy routing and deployed infrastructure acceptance remain open.
