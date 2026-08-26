# External Retainer Contract — Binding Terms (Solo Adaptation)

## Parties
- **Principal**: SentinelLayer (Founder)
- **Retainer**: External vCISO / IR provider (to be contracted)

## Scope (3 functions)
1. **CSIRT / Incident Response** (Section 14.15)
   - Severity HIGH: response < 1 hour
2. **Dual-Control Approval** (Section 14.18)
   - Planned High: approval < 4 hours
   - Planned Medium: approval < 24 hours
3. **Independent Verification / Peer Review** (Section 0.4)
   - Asynchronous review of critical changes and post-action reviews

## SLAs
| Event | SLA |
|-------|-----|
| Security incident HIGH | < 1 hour |
| Emergency post-action review | < 24 hours |
| Planned change approval (High) | < 4 hours |
| Planned change approval (Medium) | < 24 hours |

## Access
- Read-only access to audit log and evidence store
- No write access to production systems

## Fees (indicative)
- Retainer: USD 1,500 – 5,000 / month (bundled)
- Year-1 budget envelope: USD 18,000 – 60,000 (see Section 33.4)

## Non-Compliance Consequences
- Missed SLA by Retainer → contractual penalty / replacement
- Missed log submission by Founder → automatic REJECTED status + alert

## Status
**PENDING CONTRACT SIGNATURE** — required before any P0 requirement can reach ACCEPTED (Independent Reviewer VALID check).
