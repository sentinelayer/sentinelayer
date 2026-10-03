# Capacity series and session cleanup — 2026-10-03

## Implemented and verified

Verifier code `5870829163a2744c515726846900e16f9dc79086` passed all seven GitHub workflows and 13 relevant tests. API remains on verified code `4cf556f` / deployment `31ef4a72-118a-4076-9bc4-d748211f8564`; verifier-only changes were not unnecessarily deployed to the API.

- Bounded series: at most 20 rounds / 20,000 requests, concurrency at most 32. No new round is scheduled after a transport error or the five-minute scheduling budget. Each round retains its complete failures and processing samples.
- The HTTP verifier pool retains at most 32 live/idle connections rather than churning a default 20-idle pool under 32-thread concurrency.
- Network exceptions are recorded separately from received degraded responses and policy mismatches. Only exception type/numeric errno is logged; exception messages, URLs, tokens and credentials are withheld.
- Failed series now exits nonzero. Railway job status is not substituted for performance evidence.
- Owner logout runs even if owner/alert/policy inspection fails. If public egress fails, private cleanup verifies JWT signature and claims, then targets one exact token/user/tenant/email session through the verifier-only database credential. Forged tokens and unrelated sessions were covered by tests. This DB fallback was not needed in the successful live cleanup and is not claimed live-verified.
- The one session left by the failed first series was narrowly identified by its recorded UTC login window and revoked through the authenticated owner API. Other sessions were preserved. The second series's owner session was logged out normally.

## Local profile

20,000 requests / concurrency 32 / real Redis and two workers per engine: all HTTP 200, zero degraded responses and baseline errors, processing p95 **13.366580 ms**. Gateway duration **36.943 seconds** (~541 requests/second). This is synthetic, distinct-path tenant simulation without signed-policy deployment validation. It is not a production capacity certification.

## Actual deployed series

The first series, deployment `9d0ff156-4984-4d0d-b7c1-526416c1b1a6`, failed: 6,390 requests returned 200 and 13,610 raised ConnectError. Its logout also failed. The original exception logging did not establish the root network cause. Those transport errors were originally counted as degradation/policy mismatches; the raw evidence retains that original interpretation rather than rewriting history.

After verifier connection-pool/diagnostic/cleanup changes, deployment `87d8d006-59ed-485d-a3c7-53749e54b009` completed **20,000 HTTP 200** over **85.541 seconds** at concurrency 32: zero transport errors, zero degraded responses, zero policy mismatches, policy version 3 throughout. MFA, signed deny/boundary, gateway receipt, previous-session cleanup and final owner logout passed.

**Strict window latency gate remains FAIL.** Eighteen rounds met processing p95 <20 ms; round 5 measured **25.398345 ms**, and round 19 measured **22.962448 ms**. The report does not infer an aggregate percentile from individual percentiles. Client wall times include network/upstream time and are distinct from gateway processing.

The API remains SUCCESS; the private one-shot verifier is CRASHED because its capacity gate correctly exited nonzero. It has no cron and restart NEVER. Probe flags were disabled for subsequent deployments (`PILOT_CAPACITY_PROBE=0`, rounds=1), and the previous-session cleanup window was cleared without triggering another deployment. No load job remains running or scheduled.

## Remaining gates and dependencies

- Window latency at this deployed workload remains unaccepted. Do not hide two failed windows or replace them with the passing local profile. Longer hours/days of tenant traffic are also not certified.
- User selected Slack for real alert routing. Plugin connection is still unconfirmed; no Slack credentials, receiver or real delivery have been fabricated.
- [HA expansion assessment](ha-expansion-2026-10-03.md) specifies the minimum PostgreSQL topology and migration/rollback checks. Existing service/volume constraints cannot accommodate that cluster. API and Redis redundancy remain separate requirements.
- Representative customer-held-out traffic, independent security/legal review and independent off-account DR remain external acceptance gates.

Raw evidence: `evidence/tenant-profile-deadline-20000-32.json`, `evidence/deployed-series-first-failure-2026-10-03.json`, `evidence/deployed-series-rerun-2026-10-03.json`. Earlier failed profiles remain available.
