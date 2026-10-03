# Verification follow-up — 2026-10-03

## Changes

Redis engine connections now have 200 ms connect/read bounds. Tenant correlation stores one last-seen member per known signal type and 61 one-second event-count buckets, with 65-second expiry. Update and observation use one atomic Redis script. Legacy event JSON remains readable until its 60-second window expires. Event counts have one-second precision; type correlation remains based on last-seen timestamps.

Webhook delivery uses an atomic database lease and recovers expired claims. The retry budget survives worker crashes. Delivery remains at least once: receivers must deduplicate the stable X-Sentinel-Delivery identifier.

The isolated backup restore drill can reapply database-specific service grants and verify tenant isolation, authentication reads, and worker reads. Grant-only mode refuses active databases and does not alter cluster-wide role credentials. New full-schema PostgreSQL CI coverage checks credentials remain unchanged.

## Local evidence

- Python unit suite: 154 passed, 16 integration tests deselected.
- Real Redis: bounded history and legacy transition regression passed.
- Silent Redis TCP peer: behavior and risk fail within one second.
- Webhook: concurrent claims, abandoned claim recovery, and exhausted retry budget passed.
- Gateway engine-failure/recovery, signed-policy and host/tenant end-to-end drills passed.
- Tenant simulation, 5,000 requests / 8 concurrent connections: processing p95 14.181 ms; no HTTP failures or degraded responses.
- Tenant simulation, 5,000 / 32: both recorded runs FAILED the strict 20 ms processing gate. Before atomic observation: p95 42.775 ms. After: p95 49.210 ms, four request timeouts and 61 degraded responses. These are retained, not omitted.

Capacity profiles use synthetic X-Tenant-ID scoping and distinct paths; they do not establish signed-traffic production capacity, sustained throughput, availability or an SLA. Runtime variability prevents a causal speedup claim.

## Remaining gates

This follow-up is not general-availability certification. Representative held-out detection/false-positive calibration, deployed sustained tenant capacity, managed failover, real alert recipient delivery, independent off-account recovery/key custody/retention, and independent security/legal review remain open. Synthetic WAF samples are regression tests, not customer accuracy evidence. 

## Deployed verification

Code commit `5074470f169928745773fc23720aa228fd5759f5`: all seven GitHub workflows succeeded, including full PostgreSQL schema/grant restore. API deployment `5c08cc7a-cdf2-4d6f-be01-89c3bc0db3be` succeeded; runtime UID1000, durable policy floor3, Redis engines and database readiness passed. Live health/readiness 200, signed deny403, boundary200.

Backup restore deployment `c76b8300-b2ff-4ca5-bcc1-7e73c962ece9` authenticated encrypted bucket readback, restored33 tables at schema0028, matched snapshot counts, reapplied restricted grants and passed runtime tenant isolation/auth/worker reads. Temporary database removed. Private verification deployment `f4330caa-71c5-4224-abea-e458432b9761` passed owner MFA, deny boundaries, gateway receipt version3 and session revocation.

Daily backup deployment `ea678cf7-932b-4f70-80ba-bdd0d2383ce8` succeeded with cron `0 3 * * *` restored. Drill flags were staged as0; OAuth access withholds variable values, so direct value readback is unavailable. All five services report SUCCESS. Raw non-secret proof: [deployed follow-up evidence](evidence/deployed-followup-2026-10-03.json). Daily schedule readiness does not imply tomorrow's execution has already occurred.
