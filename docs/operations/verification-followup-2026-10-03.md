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

This follow-up is not general-availability certification. Representative held-out detection/false-positive calibration, deployed sustained tenant capacity, managed failover, real alert recipient delivery, independent off-account recovery/key custody/retention, and independent security/legal review remain open. Synthetic WAF samples are regression tests, not customer accuracy evidence. PostgreSQL CI and the new deployed grant-aware restore must be checked before claiming those checks passed.
