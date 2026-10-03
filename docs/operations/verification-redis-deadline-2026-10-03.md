# Redis deadline hardening and deployed capacity verification — 2026-10-03

Code commit: `4cf556f0522d482f7a616a65d2285853a2739ccc`.

## Redis outage regression

The rate limiter supplied a 100 ms context but go-redis context timeouts were disabled by default. A TCP peer accepting connections without replying held a request for **5.006 seconds**. The regression test failed before the fix.

Explicit 100 ms dial/read/write/pool timeouts, context deadline handling, disabled automatic retries and a bounded 64-connection pool now bound the operation. The silent-peer regression passes with a 500 ms test ceiling. Infrastructure errors still propagate to the existing endpoint-specific fail-closed policy. The rate threshold and Lua atomicity remain unchanged.

Validation: all Go tests and `go vet ./...` passed; six pilot measurement tests passed; five real-Redis engine/API tests and all three gateway failure/signed-policy/host-isolation drills passed; all seven GitHub workflows passed for the code commit.

## Actual deployed probe

Verifier deployment `65f89bc7-188b-4a4b-b42c-79438a7721c9`, against API deployment `12241255-f735-41cc-9e31-4fd7ac138e37` (API code `15b6a89`).

- 1,000 authenticated requests, concurrency 32, elapsed 2.948 seconds.
- 1,000 HTTP 200; zero failures, degraded responses or policy mismatches.
- 1,000 trusted processing samples; p95 gateway processing **11.955911 ms**.
- p95 verifier client wall time **205.515884 ms**.
- Owner MFA, signed deny/boundary, authenticated policy receipt version 3 and owner-session revocation passed.
- Read-only alert inspection: zero registered webhook receivers and zero recent deliveries.

A preceding verifier run (`be02f2e0-4021-4b07-86d7-cdda74c0b2fa`) failed before MFA with a sanitized RuntimeError. Its old logging did not identify the HTTP status; its deployment SUCCESS is not a verification pass. The subsequent run passed after adding safe route/status diagnostics. No authentication bypass or credential change was introduced.

This short probe does not certify sustained capacity, HA, availability SLA or customer accuracy. Previously failing 20,000-request local results remain in the evidence directory and are not superseded by this short pass. Real receiver delivery remains unverified until a receiver is configured. Existing single-instance infrastructure and independent restore/traffic-review gates remain open.

## Hardening deployment

API deployment `31ef4a72-118a-4076-9bc4-d748211f8564` succeeded with code `4cf556f`, runtime UID 1000, database readiness HTTP 200 and durable policy floor version 3 restored. API restart policy is ON_FAILURE with ten retries. PG, Redis and backup configuration was not changed in this deployment.

Post-deployment verifier `fc6c3aea-d7dd-425c-a50f-85c09a3cb5c2` passed MFA, signed deny/boundary, receipt version 3 and owner-session revocation. Its 1,000-request / 32-concurrency probe completed in 3.487 seconds: all HTTP 200, zero degraded/failures/policy mismatches, processing p95 **15.976098 ms**, verifier wall p95 **232.067512 ms**. Alert registration count remains zero. Neither short probe proves that the earlier sustained-load failures have been resolved.
