# ADR 0002: Policy Signing Hierarchy

## Status
Accepted

## Context
Unsigned or tampered policy must never activate (P0: SL-SEC-POLICY-001). Solo founder needs automatic rotation without dual-human ceremony every time.

## Decision
- Root/policy signing key hierarchy
- Active signing key rotates every 24h automatically
- Previous key retained for verification window
- Only signatures from current or retained keys accepted
- Activation path rejects unsigned policy (fail-closed)

## Consequences
- Key rotation worker required (already scaffolded)
- Evidence must record which key version signed a policy
- Compromise model: rotate + revoke window documented in operations
