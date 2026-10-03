# HA expansion assessment — 2026-10-03

## Verified current environment

Project `focused-enthusiasm` uses five services and three persistent volumes under the previously reported five-service / three-volume account limits. The connector does not expose the current billing-plan label, so this assessment does not assert that the workspace is paid Hobby. API, PostgreSQL and Redis each run a single instance. The daily encrypted backup bucket is in the same Railway account and is not independent disaster recovery.

PostgreSQL configuration is the official pinned `ghcr.io/railwayapp-templates/postgres-ssl:18` image, with no custom start command. Railway exposes the `postgres-ha` conversion configuration for this service. PostgreSQL 18 is supported by the current full documentation; a search excerpt limited to 16/17 is not the authoritative support list.

## Concrete infrastructure requirement

The minimum PostgreSQL conversion keeps the original primary and adds two streaming replicas, three etcd coordinators and two HAProxy instances. This requires seven additional services: **at least 12 total services** alongside the four existing non-PostgreSQL services. The default three HAProxy instances would bring the total to 13. PostgreSQL/etcd persistent volumes also exceed the current three-volume quota. Redis redundancy and API redundancy would be additional work and cost.

Railway documents a volume backup before conversion, dropped active connections and changed connection endpoints. Variable references are migrated automatically; literal URLs require explicit replacement. SentinelLayer uses restricted role-specific database connections, so every API/auth/worker/backup connection must be checked after migration; a root database URL must never replace a restricted runtime URL.

Do not deploy a partial cluster under the current quota or describe multiple API processes as HA. Merely raising the API replica count is insufficient: the mounted durable policy floor and gateway instance/receipt identities require a replica-safe design first.

## Execution and acceptance sequence

1. Approve sufficient service/volume capacity and a usage budget for the reviewed cluster. No plan upgrade or cluster conversion was performed during this assessment.
2. Verify a fresh encrypted backup with an isolated restore, tenant isolation and restricted-role grants. Preserve the old connection configuration for rollback without publishing secrets.
3. Stage the supported PostgreSQL HA conversion, inspect every new service/volume and role-specific connection change, then deploy within a recorded maintenance window.
4. Verify primary/replica/coordinator/proxy health; replay MFA, signed policy, tenant isolation and write/read checks through HAProxy.
5. Deliberately switch the leader, record observed interruption and reconnection behavior, and measure RTO/RPO. Do not assign an SLA from the provider's descriptive documentation.
6. Design and separately verify Redis failover and replica-safe gateway policy floors before approving end-to-end HA.
7. Keep independent off-account backup/key custody, retention and restore evidence as separate gates.

Official sources reviewed: https://docs.railway.com/databases/postgresql-ha and https://docs.railway.com/pricing/free-trial . The published trial limits match the observed five-service / 1 GB constraints; matching limits alone are not proof of the account billing state. This file is a reviewed implementation path, not evidence that HA is deployed or failover has passed.
