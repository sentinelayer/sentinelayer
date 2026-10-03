# Async engine performance verification — 2026-10-03

## Implementation

Production behavior/risk HTTP endpoints and health checks now await asynchronous Redis clients rather than dispatch synchronous Redis calls through the web server thread pool. Shared Lua scripts and result parsers preserve frequency/sequence thresholds, correlation multipliers, tenant scoping and legacy history transition. Redis connect/read bounds remain200ms; client pools are capped at64 connections per process, and async clients close at application shutdown. Gateway per-request deadlines and circuit-breaker behavior are unchanged. Critical shared-state failures still deny; normal requests retain explicit unavailable/degraded markers.

Gateway processing/stage timing is emitted to the upstream and returned through trusted `X-SL-Gateway-*` response headers. The proxy overrides upstream timing/degraded values using headers set after its own pipeline. E2E checks inject forged client/upstream values and require authentic replacement. Processing timing ends before upstream execution; it is not end-user response latency.

`verify_pilot.py` can perform an explicitly enabled bounded deployed capacity probe:100–1,000 requests,1–32 concurrent clients, owned pilot HTTPS origin only, authenticated owner session and exact signed policy version. The report requires complete finite timing samples, HTTP200, no degraded responses and no policy mismatches. Missing/NaN timing or a failed class cannot pass. Capacity gate outcome is separate from the MFA/policy correctness result; job SUCCESS alone does not certify performance.

## Local measurements

All profiles are synthetic distinct-path tenant simulations with fresh client connections. They do not establish customer traffic accuracy, signed-policy capacity or sustained deployed availability.

| Profile | Processing p95 | HTTP failures | Degraded | Gate |
|---|---:|---:|---:|---|
| Sync,5,000/32 |38.884ms|0|0|FAIL|
| Async,5,000/32 |12.171ms|0|0|PASS within local scope|
| Async,20,000/32 |16.827ms|0|0|FAIL overall:baseline had2 connection timeouts|
| Async,20,000/32, fixture accept queue128 |20.984ms|0|4,328|FAIL|

The initial stage profile had WAF p952.962ms, behavior21.746ms and risk19.652ms. The first async profile had WAF2.654ms, behavior5.654ms and risk4.837ms. These are separate stage distributions and cannot be summed to infer request p95. Runtime variability and longer-run failures prevent a sustained20ms claim. All raw reports, including failures, remain in `evidence/`.

The fixture's default five-connection accept backlog caused baseline timeouts independently of gateway processing; it is now128. The subsequent result remains a failure and is not hidden. Public processing headers allow checking the actual deployment independently of internet round-trip delay and the local fixture.

## Verification and open gates

Local unit suite:163 passed,17 integration tests deselected. Real Redis tests exercise both sync/async observation and actor/tenant isolation. Silent Redis peers fail within one second for both clients; critical async failures retain deny semantics. Go tests/vet and engine outage/recovery, signed policy/receipt and host-routing drills are checked separately before publication.

Representative held-out traffic, real production alert recipient delivery, managed failover, independent off-account recovery/key custody/retention and external security/legal review remain open. Existing local encrypted/HMAC webhook transport and restricted grant-aware backup restore evidence retains its limited scope. This change is not general-availability approval.
