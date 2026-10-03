# Signed-policy refresh concurrency fix — 2026-10-03

Code commit `fc7767591b6c3ddc0f9b779b9f57443eb2a1d07f` passed all seven GitHub workflows, Go tests/vet, policy-package race tests, 15 verifier measurement tests, five real-Redis engine/API tests and all three gateway failure/signed-policy/host-isolation E2E drills.

## Independently reproduced bottleneck

The policy cache held its mutex while fetching the signed bundle over HTTP. A concurrency regression blocked the control-plane response and demonstrated that another request with an unexpired verified policy waited behind that network operation. The test failed before the fix.

The cache now coordinates one in-flight refresh while releasing the cache mutex for network I/O. The refresh initiator still waits for verification and installation; other requests may use only an existing verified, unexpired snapshot while that refresh is running. Cold/expired requests wait for the shared result and honor their context cancellation. Expiry, tenant binding, signatures, rollback floors and durable floor installation remain enforced. No TTL, refresh interval, deadline or risk threshold was relaxed.

The new warm-cache concurrency test passes and confirms that the refresh installs the higher version with only one HTTP fetch. The expired-cache test verifies cancellation and refusal of an expired policy. Existing forged signature, rollback, expiry-during-fetch and durable-floor tests remain green under the race detector.

Gateway trusted telemetry now includes rate-limit and policy stages. Upstream/client-supplied timing is overwritten. The verifier records complete stage sample counts and exact aggregate processing p95 from all finite samples, while preserving the strict requirement that each 1,000-request window pass independently. A regression verifies that a passing aggregate cannot hide a failed window.

## Deployment

API deployment `0565842e-348d-4154-9103-96f61c0f273d` succeeded. Startup validated configuration, ran as UID 1000 and restored durable signed-policy floor version 3. PostgreSQL, Redis and backup services were not changed.

## Before-fix diagnostic deployment

API code `f289f8e`, verifier code `304dc1c`, job `43448a54-8d0e-4976-8c2d-b2976982ffd1`: 20,000 HTTP 200, zero errors/degraded/policy mismatches, 20,000 processing samples, exact aggregate p95 **19.416079 ms** over **68.812 seconds**. The aggregate met 20 ms, but eight individual windows exceeded 20 ms; strict window gate remained FAIL. Client wall time and component percentiles are separate distributions and must not be combined to infer per-request overhead.

The lock regression establishes a real serialization defect; it does not establish that every slow deployed window had that sole cause. The raw diagnostic evidence retains the independently measured stage distributions.

Post-fix deployed results are recorded below. Slack receiver connection, capacity/HA expansion, representative held-out customer traffic and independent review remain separate gates; no GA or SLA certification is implied by this fix.


## Post-fix deployed result

Private verifier deployment `d423f7af-b1a8-4c1b-91e9-b8a8dab5e80e` completed all **20 rounds / 20,000 authenticated requests at concurrency 32** in **76.538893 seconds** against the already successful API deployment above. Every response was HTTP 200, with zero transport failures, degraded responses or policy mismatches. Every round contained 1,000 complete finite samples for WAF, rate limiter, signed policy, behavior and risk stages.

Exact aggregate processing p95 from all 20,000 samples: **8.257220 ms**. Every window independently passed <20 ms; the worst window p95 was **12.270482 ms**. The strict series gate is PASS. Owner MFA, signed deny/boundary, authenticated gateway receipt version 3 and final owner-session revocation also passed. No old failed window or transport-error series was removed.

After completion, probe flags were disabled for subsequent deployments, rounds reset to one and the old cleanup window cleared without redeploying. The job has no cron and restart NEVER. This ~77-second test meets its bounded workload gate; it does not certify hours/days of sustained traffic, HA, uptime SLA, representative customer accuracy or independent security review. Network/workload variation prevents attributing every measured improvement solely to the policy mutex change.

Raw evidence: [before-fix diagnostics](evidence/deployed-series-diagnostic-before-policy-fix-2026-10-03.json) and [complete post-fix result](evidence/deployed-series-policy-refresh-fix-2026-10-03.json).
