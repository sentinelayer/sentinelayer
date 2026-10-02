# Signed gateway runtime policy

This is opt-in policy enforcement with either a default single-tenant binding
or explicit operator-configured hostname bindings for several tenants.
The existing built-in WAF/auth/rate/risk pipeline remains active.

## Configure

1. As a tenant administrator, create a policy with an explicit `gateway` object:

```json
{"name":"edge","rules":{"gateway":{"mode":"enforce","block_score":80,"deny_path_prefixes":["/private"]}}}
```

2. Create an expiring API key for a dedicated active service account in that
   tenant. Read access is tenant scoped; API keys cannot perform privileged
   policy mutations. Fine-grained policy-read-only API key scopes are not yet
   available, so isolate and rotate this credential.
3. Configure the gateway with these deployment-owned values:

```dotenv
GATEWAY_POLICY_URL=https://control-plane.example/api/v1/policies/POLICY_ID/runtime
GATEWAY_POLICY_API_KEY=YOUR_SERVICE_ACCOUNT_KEY
GATEWAY_POLICY_ID=POLICY_ID
GATEWAY_POLICY_TENANT_ID=TENANT_ID
POLICY_SIGNING_PUBLIC_KEYS_JSON={"YOUR_SIGNING_KEY_ID":"YOUR_BASE64_ED25519_PUBLIC_KEY"}
```

Pin public keys obtained through the deployment's trusted key management.
Never learn trust automatically from the policy response. HTTPS is required
except numeric loopback HTTP. Loopback must address the backend directly, not
the enforcing gateway, to avoid recursion. Redirects and environment proxies
are disabled; credentials are sent only as `X-API-Key`.

The export endpoint refuses unsigned/tampered stored versions, missing gateway
rules, unsupported fields/modes and ambiguous path prefixes. It signs canonical
payload bytes containing tenant, policy, application, version, issue time,
expiry and validated rules. The gateway verifies these exact bytes before
parsing; no cross-language JSON reserialization is used for signature checks.

## Runtime behavior

- Refresh on requests at most every ten seconds while a valid snapshot exists.
  Bundles have a 60-second signed lifetime; issue-time checking allows up to
  30 seconds of positive clock skew. Synchronize clocks on both services.
- Fetch timeout is 800 ms, response size is capped at 64 KiB, and only known
  signing keys and matching tenant/policy identities are accepted.
- An unexpired verified snapshot can survive refresh/network/signature failure.
  When none is usable, traffic receives `503 POLICY_DEPENDENCY`; dependency
  failure never creates an allow policy. `/health` reports process liveness,
  not policy availability. Alert on `policy_dependency` blocks and perform a
  protected traffic probe during rollout.
- Authenticated traffic from another tenant receives `403 POLICY_TENANT`.
  Anonymous context binds to the configured tenant rather than trusting headers.
- Enforce mode blocks at `score >= block_score` or a matching deny prefix.
  `/private` matches `/private` and `/private/...`, not `/private-ish`.
  These rules apply even to public endpoints. Monitor mode skips these additional
  policy blocks; it does not disable WAF, authentication or rate protection.
- Responses/upstream requests carry `X-SL-Policy-Version`; blocked decision JSON
  records the actual policy ID/version. Risk fallback caches include this version.
- Older versions cannot replace the current snapshot in the same process.
  Roll back through the API's rollback operation, which creates a new higher
  version. Configure `GATEWAY_POLICY_STATE_DIR` on a durable volume to retain
  the version floor across restarts; otherwise the floor is memory-only.

Leaving all `GATEWAY_POLICY_*` values unset uses the built-in pipeline with
`builtin-v1` decision provenance. A partial binding fails startup.

## Evidence and limits

Go tests cover signatures, bindings, expiry (including expiry while fetching),
version rollback, cache fallback expiry, path boundaries and invalid config.
The signed-policy E2E uses the real API handlers and API-key middleware with an
isolated SQLite database, a real Go gateway, real Redis, risk and behavior
services. It proves Python-to-Go verification, tenant/deny enforcement, forged
signature rejection, higher-version adoption and WAF blocking in monitor mode.
Host-routing E2E additionally exercises two tenant policies, unknown-host
rejection, spoofed tenant/forwarded-host headers and authenticated policy receipts.
It does not prove deployment networking, managed key rotation or the honesty of
a compromised registered gateway. See [fleet delivery](gateway-policy-fleet.md).
