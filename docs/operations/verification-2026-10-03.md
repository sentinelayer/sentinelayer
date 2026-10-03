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

- Processing p95 at concurrency 32 fails; define and verify a sustained supported
  operating envelope before committing to throughput/latency guarantees.
- Representative held-out detection/FP calibration and customer pilot evidence.
- Managed Redis/PostgreSQL interruption, replacement restore with role grants,
  alert delivery and incident response evidence; the current single replica is
  not HA.
- Independent recovery copy/key custody and retention lifecycle. Existing bucket
  backup/restore succeeded, but same-account backup cannot prove account-loss DR.
- Independent security/legal review and real customer acceptance when required
  for GA; synthetic accounts cannot substitute for customers or their consent.

## Local regression results

150 Python tests passed (14 integration tests reserved for PostgreSQL CI); all
Go packages passed, go vet passed, all four dashboard MFA tests passed, and
TypeScript/Vite build passed. Signed-policy and host-routing E2E passed using
the real Python policy API and Go signature verification.
