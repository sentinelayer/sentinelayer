# ADR 0003: Fail Open vs Fail Closed

## Context
Security capabilities may fail during runtime.

## Decision
- WAF: Fail Open (availability > security)
- Auth: Fail Closed (security > availability)
- Rate Limit: Fail Open
- Risk: Fail Open
- Decision: Fail Closed

## Alternatives
- All fail closed - too many outages
- All fail open - insecure

## Consequences
- Different behavior per capability
- Documented in fail-matrix.yaml
- Last-known-good fallback
