# Production PostgreSQL role separation

Production uses three non-owner, non-superuser, NOBYPASSRLS identities. Authentication and maintenance have explicit service policies only on the tables their jobs need. Tenant API sessions retain transaction-local RLS context across commits/rollbacks.

| Connection | Identity | Scope |
| --- | --- | --- |
| `DATABASE_URL` | `sentinel_app` | Tenant-scoped API records; no bootstrap grants; append-only audit writes |
| `AUTH_DATABASE_URL` | `sentinel_auth` | Tenant registration, identity, sessions, API keys and bootstrap grants; no application/policy data |
| `WORKER_DATABASE_URL` | `sentinel_worker` | Evidence expiry, offboarding and webhook delivery tables; no user/authentication tables |
| `MIGRATION_DATABASE_URL` | Deployment-owned migration identity | DDL and role provisioning; available only to a separate migration/provisioning job |

## Provisioning

Use a dedicated SentinelLayer database. The provisioning script revokes public schema CREATE and resets direct table/sequence grants for the three named roles. Review existing role memberships and shared grants before applying it; production startup rejects service-role membership, owner membership, CREATE privileges and elevated identities.

1. In an isolated migration job, inject `MIGRATION_DATABASE_URL` and run `alembic -c alembic.ini upgrade head`.
2. Inject `RUNTIME_DATABASE_PASSWORD`, `AUTHENTICATION_DATABASE_PASSWORD` and `WORKER_DATABASE_PASSWORD` from the secret manager (at least 24 characters each). Run `python scripts/configure_database_roles.py`. Passwords are never printed or committed.
3. Configure the API/worker environment with the three service URLs targeting that database. Set `SL_ENV=production`, `SL_AUTO_CREATE_SCHEMA=0`, and `SL_RUN_STARTUP_MIGRATION=0`. Keep migration credentials out of this environment; production refuses them.
4. Restart only after migrations/provisioning succeed. Re-run provisioning after migrations introduce new tables or worker permissions. No default future-table grants are issued.

Development can retain the original shared DATABASE_URL and optional startup migration. Railway no longer runs privileged migrations from the application service automatically; use a separate migration service/job with its own secrets. An existing deployment must be updated before switching to production mode.

## Evidence and limits

CI runs a production-mode API using the three real PostgreSQL service roles. It verifies startup, auth/login/logout, owner access, BOLA/list isolation, direct RLS filtering after commit, forbidden DDL/role escalation, limited authentication/worker table access, and a maintenance cycle. This is a disposable CI deployment; managed PostgreSQL role setup, staging rollout and restoration still need verification on deployment infrastructure.

Authentication and worker credentials intentionally have wider visibility within their narrow table sets. Pool separation protects the tenant data connection; all processes in the single-service image still share one OS identity and can read the process environment. Process/container isolation and separate secret injection are required if the threat model includes arbitrary code execution in the API process. This configuration does not claim to contain such a compromise.
