# Behavior and delivery follow-up — 2026-10-03

## Changes and contract

Behavior Redis history now retains at most51 newest events per tenant/actor with a five-minute event window and305-second key expiry. The newest51 events preserve every frequency threshold (>20 elevated, >50 critical), including after partial expiry; sequence analysis still reads the newest50 actions. Atomic Lua observation replaces the multi-command transaction. Frequency count51 is a lower bound, explicitly reported as `count_is_lower_bound=true` with `retained_count_limit=51`. It must not be displayed as an exact request total or used for billing. Counts below51 are exact for the event window. Existing large histories are trimmed on their next observation.

Offline WAF calibration now accepts sanitized labelled corpora and reports per-case verdicts, digest and uncertainty. See [calibration](calibration.md). Synthetic data remains regression-only; production acceptance is never inferred automatically.

## Verification

- Real Redis:1,000 actor requests, threshold transitions, partial/full expiry, actor/tenant separation, maximum51 stored entries, and fraud-sequence detection passed.
- Real Redis correlation regression and gateway outage/recovery, signed-policy hot update, authenticated receipt and host/tenant-routing drills passed.
- Webhook queue-to-local-receiver test passed with real SQLite queue, encrypted secret, HMAC validation, HTTP503 retry then202 acknowledgement, persisted delivery completion and no re-send of completed rows. Only destination validation was replaced to reach the local test receiver; production still rejects loopback/private addresses. Existing real HTTP/TLS pinning and redirect rejection tests also passed. This is not production alert-recipient delivery evidence.
- Current tenant synthetic capacity:5,000 requests at32 connections, p95 processing36.233ms, zero HTTP failures/degraded responses: strict20ms gate FAILED. At8 connections, p95 processing33.761ms, zero HTTP failures, two degraded responses: gate FAILED. The8-connection baseline overlapped a brief independent webhook test, so it is not an isolated SLO measurement. Both complete raw reports are retained. Earlier passing runs do not override these failures.

## Acceptance

Resource-bounded history and queue delivery mechanics are verified in the described scope. Overall production acceptance remains open: repeatable sustained deployed tenant performance, representative held-out customer calibration, managed failover, actual recipient alert delivery, independent recovery/key custody/retention, and external security/legal review. Do not promise20ms or an SLA from these results.

## Published and deployed evidence

Code commit `82adaa95bced5da18aeec3da4ccaf5f82b8490f1`: all seven CI workflows succeeded. Local suite: 155 unit tests passed, 17 integration tests deselected; real Redis integration tests and gateway drills were run separately and passed. Go tests and vet passed, including calibration label validation and confidence bounds.

API deployment `debc5dcf-a7c1-4153-b66c-cd3d0747c186` succeeded using the explicit Dockerfile builder, runtime UID 1000, healthy database/Redis engines and durable policy floor 3. Live health/readiness returned 200, signed deny 403, and path boundary 200. Private verifier `6b07a449-b956-4cf0-840e-406c180efbec` passed owner MFA, signed deny boundary, authenticated receipt version 3 and session revocation. All five services report SUCCESS. Existing daily backup remains scheduled at `0 3 * * *`; it was not rerun by this behavior-only deployment. [Non-secret deployment evidence](evidence/deployed-behavior-2026-10-03.json).
