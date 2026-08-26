# Definition of Done (DoD) — Section 0.1

Every requirement **must** contain the following fields. Missing any field → cannot enter Gate evaluation.

| Field | Description | Example |
|-------|-------------|--------|
| Requirement ID | Unique stable ID | `SL-SEC-AUTH-001` |
| Owner | Accountable person/role | `Founder` |
| Dependency | List of prerequisite Requirement IDs | `["SL-SEC-ID-001"]` |
| Requirement | Clear statement of what must be true | `All API endpoints require valid JWT or API key` |
| Acceptance Criteria | Testable conditions | `Unauthenticated request → 401; malformed JWT → 401` |
| Security Impact | What happens if violated | `Unauthorized access to tenant data` |
| Test Method | How it is verified | `Automated integration test + adversarial matrix` |
| Failure Behavior | What the system does on failure | `Fail-closed for Critical API; MONITOR for Normal` |
| Rollback Strategy | How to undo | `Revert to previous signed policy version within 15 min` |
| Evidence | Evidence IDs that prove it | `["EV-AUTH-001", "EV-AUTH-002"]` |
| Reviewer | Independent reviewer | `External Retainer` (solo adaptation) |
| Criticality | P0 / P1 / P2 / P3 | `P0` |
| Gate | MVP / Pilot / Production / Enterprise | `MVP` |
| Status | Derived by Gate Engine only | `NOT_STARTED → … → ACCEPTED` |

## Status Machine (machine-enforced)
Status is **never** set by human write. Only GateEngine.evaluate() may produce ACCEPTED or REJECTED.

## Production Ready Rule (0.3)

`PRODUCTION READY` = true **only if**:
1. All P0 + P1 requirements have status = ACCEPTED
2. Coverage of P0+P1 ≥ 95%
3. Any non-accepted items have documented risk acceptance + mitigation plan
