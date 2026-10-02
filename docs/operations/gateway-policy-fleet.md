# Host policy routing and gateway delivery reports

## Host bindings

Use either the existing four default `GATEWAY_POLICY_*` variables, or the
following host map. Mixing modes fails startup. Public keys remain pinned in
`POLICY_SIGNING_PUBLIC_KEYS_JSON`.

```json
[
  {"host":"tenant-a.example","url":"https://cp.example/api/v1/policies/POLICY_A/runtime","api_key":"SERVICE_A_KEY","policy_id":"POLICY_A","tenant_id":"TENANT_A"},
  {"host":"tenant-b.example","url":"https://cp.example/api/v1/policies/POLICY_B/runtime","api_key":"SERVICE_B_KEY","policy_id":"POLICY_B","tenant_id":"TENANT_B"}
]
```

Put this JSON in the deployment secret `GATEWAY_POLICY_BINDINGS_JSON`, since it
contains service API keys. At most 100 DNS hostname bindings are allowed.
Unknown hosts return `421 POLICY_ROUTE`; duplicate hosts and ambiguous duplicate
tenant/policy identities fail startup. Host aliases for the same identity share
one client/cache and must use the same endpoint/credential.

Routing uses the request's actual Host, ignoring `X-Tenant-ID` and
`X-Forwarded-Host`. Preserve and validate Host at the trusted HTTPS ingress.
Authenticate private traffic with valid gateway JWTs: cross-tenant identities
return 403. Backend-only API keys or invalid bearer tokens cannot establish the
gateway's tenant binding and return `401 POLICY_AUTH`. The control-plane service
API key used to fetch policies addresses the backend directly.

All host bindings still use the configured `UPSTREAM_URL`. This is policy
routing, not an arbitrary upstream/proxy map. The upstream must independently
enforce tenant authorization. DNS/HTTPS onboarding and trusted-proxy addressing
remain deployment requirements.

## Register and report

As an MFA-verified tenant administrator, call:

```http
POST /api/v1/policies/POLICY_ID/gateways
{"gateway_id":"edge-01","service_user_id":"ACTIVE_TENANT_SERVICE_ACCOUNT_ID"}
```

Then configure that gateway with:

```dotenv
GATEWAY_INSTANCE_ID=edge-01
GATEWAY_POLICY_ACK_URL=https://cp.example/api/v1/gateway-policy/ack
```

Each successful verified policy refresh triggers a bounded asynchronous report
using its policy-fetch service API key. The control plane accepts only the
registered key owner, matching tenant/policy, trusted signature, valid lifetime
and stored policy rules/version. Reported versions/issue times cannot move
backward. Changing the registered account or policy clears old report state.
Only a changed reported version emits the durable `policy.gateway_reported`
event; heartbeat retries are idempotent for that event.

`GET /api/v1/policies/POLICY_ID/gateways` returns each registration with desired
version, reported version, last report, signing key and validity expiry:

| State | Meaning |
| --- | --- |
| `unreported` | No valid receipt from this registration |
| `reported` | Unexpired receipt matches the desired version |
| `lagging` | Receipt is valid but its version differs from desired |
| `stale` | Receipt's signed validity window has expired |

Reports occur on request-driven refresh; idle gateways eventually appear stale.
Report failure does not relax or disable enforcement. Monitor fleet status and
receipt rejection logs. A receipt proves an authorized service account reported
a valid signed bundle; it is not proof that a compromised gateway enforced it.
Use protected traffic probes to verify actual behavior before accepting rollout.

## Version floor across restart

Set `GATEWAY_POLICY_STATE_DIR` to a durable private volume directory owned by
the gateway/container user (`sentinel` in this image). The directory must not be
a symlink or writable by group/others; create it with mode 0700. Use one directory
per gateway process. Do not share it between independently running replicas.

Each tenant/policy gets a hashed filename with the highest verified version.
The gateway writes and fsyncs a private temporary file, atomically renames it,
then fsyncs the directory before activating a higher version. Corrupt, mismatched
or unsafe state prevents startup; persistence failure rejects the new snapshot
and permits only an existing unexpired verified fallback. Never silently delete
this state to fix startup. Rollback through the policy API creates a higher
version. Without a durable volume, restart loses the in-memory floor.

Migration `0028` adds tenant-isolated delivery records. Apply migrations and
re-provision runtime roles separately before starting the new production image.
Database-backed delivery reports and volume-backed floors need separate recovery
validation; a passing local restart test does not prove platform volume survival.
