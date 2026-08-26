# ADR 0003: Fail-Open / Fail-Closed Matrix

## Status
Accepted

## Context
When WAF, Risk Engine, or Decision Safety Layer errors, the system must not choose randomly. Matrix is versioned and signed (P0: SL-SEC-FAIL-001).

## Decision
Critical paths (auth, tenant isolation, policy load, provenance): FAIL-CLOSED.
Abuse/rate and non-critical enrichments: may FAIL-OPEN to MONITOR per signed matrix.
Matrix itself is a signed artifact; unsigned matrix is rejected.

## Consequences
- Decision Safety Layer is mandatory on the request path
- Chaos/fault tests required before Production gate
- Operational runbook must match matrix
