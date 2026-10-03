# Technical re-verification — 2026-10-03

This record is evidence of the described test scope, not production/GA approval.

## Local pipeline measurements

Real Go gateway, bundled official CRS, Python behavior/risk servers, real Redis
7.4, and a synthetic HTTP upstream ran on the same execution host. Each profile
sent 200 requests through the gateway and another 200 directly to the upstream.
Every request used a fresh connection and a distinct path. This measures short
bursts, not sustained capacity, tenant diversity, or the 60/min one-path limit.
The runs did not enable signed-policy fetching; the deployed pilot verifies that
separately. Do not infer Railway production capacity from these measurements.

| Concurrency | Gateway processing p95, ms | HTTP errors | Target <20 ms |
| --- | ---: | ---: | --- |
| 1 | 3.397 | 0/200 | Pass within this scope |
| 8 | 13.257 | 0/200 | Pass within this scope |
| 32 | 44.070 | 0/200 | **Fail** |

Processing time comes from the gateway's server-generated X-SL-Latency-Ms value
reflected by the controlled upstream. It includes pre-proxy security work and
engine round trips, excludes upstream response time and client network time.
The benchmark also records HTTP wall latency and the direct upstream baseline;
subtracting their percentiles is diagnostic, not paired request overhead.
The old benchmark silently discarded connection errors and used the last sample
as p95 for small runs. Both defects are removed. Missing server timing cannot
pass the processing latency gate.

Behavior state now fetches only the latest 50 actions with ZRANGE while keeping
the full five-minute ZCARD count. The previous implementation transferred all
history before slicing locally. A 10,000-entry regression verifies that frequency
signals retain the full count and the history transfer stays bounded. This does
not bound Redis cardinality or prove high-load production performance.

## Two-worker remediation

Runtime now defaults to two workers per engine, sharing Redis state;
SL_ENGINE_WORKERS=1 retains the smaller footprint, and startup rejects values
other than 1/2. Internal engine access logging is disabled; API/audit logging
remains enabled. The initial single-worker failed measurement above is retained.

A two-worker rerun at concurrency 32, 5,000 gateway requests, produced zero HTTP
errors, processing p95 **15.351 ms**, HTTP wall p95 **43.653 ms**, and HTTP wall
p99 **1024.025 ms** over 6.331 seconds (789.742 completed requests/second).
Subsequent runs produced processing p95 22.592 ms with concurrent regression
tests and 20.457 ms without them, both 0/5,000 HTTP errors. Both failures are
retained under evidence/. The worker change alone does not reliably meet the
processing target; the wall-time tail and short duration also prohibit a
sustained-capacity/SLA claim. Baseline/upstream,
client scheduling and fresh-connection costs are outside processing timing.
This is local evidence; Railway resource limits and signed-policy refresh load
require a deployment-specific load test before advertising those numbers.

## Detection regression

The developer-authored, labelled CRS regression corpus contains 10 attack and
10 benign inputs. All 10 attacks blocked; 0 benign inputs blocked. Cases include
SQLi, XSS, command injection, traversal, apostrophes, Unicode, Markdown and URLs.
Cases and exact rule attribution are emitted individually by Go tests.
This small hand-written corpus is **not** representative customer traffic and
cannot establish detection >95% or false positives <5% in production. A larger,
held-out, representative labelled corpus and pilot calibration remain required.

## Trust and failure testing

Signing-key overlap and revocation are exercised by Go tests: old and new keys
accepted during overlap; removal of old trust rejects old signatures while new
signatures still validate. Existing Python signing tests cover historical policy
verification during rotation. These are isolated tests, not a live key rotation.
Production rotation must retain backup decryption keys and MFA access; use the
key-compromise runbook before changing active deployment secrets.

The engine outage drill terminates only the local test-owned risk/behavior
processes, verifies critical traffic denial with a valid JWT, verifies normal
proxying and continued WAF blocking, restarts engines and verifies recovery.
The local drill passed for both engines; CI repeats it. The drill exposed a
path-wide fallback bug: a request-specific BLOCK poisoned subsequent normal
requests. The gateway now stores and reuses only ALLOW/MONITOR fallbacks; WAF
and signed policy still run on every request. It does not simulate managed Redis/PostgreSQL failover or
provide an availability/RTO measurement for Railway.

## Outstanding production gates

- Two-worker local processing p95 varies across the 20 ms gate at concurrency
  32; verify a sustained deployment operating envelope and HTTP tail latency
  before committing to throughput/latency guarantees.
- Representative held-out detection/FP calibration and customer pilot evidence.
- Managed Redis/PostgreSQL interruption, replacement restore with role grants,
  alert delivery and incident response evidence; the current single replica is
  not HA.
- Independent recovery copy/key custody and retention lifecycle. Existing bucket
  backup/restore succeeded, but same-account backup cannot prove account-loss DR.
- Independent security/legal review and real customer acceptance when required
  for GA; synthetic accounts cannot substitute for customers or their consent.

## Local regression results

151 Python tests passed (14 integration tests reserved for PostgreSQL CI); all
Go packages passed, go vet passed, all four dashboard MFA tests passed, and
TypeScript/Vite build passed. Signed-policy and host-routing E2E passed using
the real Python policy API and Go signature verification.

## Reproduce the local capacity profile

Build the gateway with `go -C gateway build -o /tmp/gateway-bin ./cmd/gateway`,
install Python requirements and Redis, then run
`python tests/gateway_capacity.py --iterations 5000 --concurrency 32 --output /tmp/capacity.json`.
The runner owns/cleans up its Redis, upstream, engines and gateway; output
contains all attempts, errors, HTTP percentiles and server processing timing.
It exits nonzero when the processing gate fails. Do not run alongside other
local tests when measuring isolated performance.

## Bounded fallback state

The gateway fallback map was unbounded and had no expiry. It now holds at most
4,096 entries with LRU eviction and a fixed 60-second lifetime. Reads cannot
extend the lifetime. Expiry and eviction are exercised by Go tests. This bounds
path-driven in-process memory growth; it does not bound Redis keys.

The engine HTTP clients now retain at most 64 connections per private origin,
with proxying disabled and existing request/circuit-breaker timeouts retained.
Intermediate runner records are corrected to state the actual one risk worker
and two behavior workers: the direct risk module entrypoint initially did not
match the two-worker launcher. Final profiles exercise both engines with two
workers, matching the deployed launcher.

## Final configuration profiles

With both engines on two workers, bounded fallback cache and pooled HTTP
connections, the 20,000-request/32-concurrency profile produced processing p95
**20.366 ms**, 0 HTTP failures, and HTTP wall p95 **43.183 ms** over 24.341
seconds. It fails the strict <20 ms processing gate.

After adding server-generated degraded-state reporting, the final 5,000-request
profile at concurrency 8 produced processing p95 **7.522 ms**, HTTP wall p95
**13.724 ms**, 0 HTTP failures and **0 degraded responses** over 5.685 seconds.
That profile passes within its local synthetic scope. A 200 response using
fallback is no longer silently counted as a healthy benchmark: the benchmark
counts X-SL-Degraded reflected by the fixture and fails on degradation.

All raw records, including failed intermediate runs, are under evidence/.
They do not establish sustained Railway capacity or justify ignoring the failed
32-concurrency gate. The final engine outage drill, signed-policy export/update,
host routing, tenant mismatch and signature-tamper E2E all passed with the two
worker configuration. Development without Redis defaults to one worker; explicit
two-worker configuration requires shared Redis state.
