# Independent Verification Rule — Solo Adaptation (Section 0.4)

## Problem
Founder must not be the sole verifier of critical code, configuration, or actions they themselves perform.

## Solution (Asynchronous Dual Control)

External Retainer (same entity as CSIRT in Section 14.15) acts as Second Party.

### Classification

| Type | Severity | Who acts first | Approval / Review |
|------|----------|----------------|-------------------|
| Emergency / Break-Glass | High | Founder (immediate) | Post-Action Review to Retainer within **24 hours** |
| Planned Change | High | Founder proposes | Asynchronous approval by Retainer **< 4 hours** |
| Planned Change | Medium/Low | Founder proposes | Asynchronous approval by Retainer **< 24 hours** |

### Non-Compliance
- Emergency action without log submitted within 24 h → status **REJECTED**, alert to Retainer
- Planned change without approval within SLA → status **REJECTED**, alert to Retainer

### Contract Binding
External Retainer must:
1. Have read-only access to audit log
2. Sign a legally binding availability contract for the SLAs above
3. Perform post-action review and return ACCEPT / REJECT with reason

See also: `docs/operations/external-retainer-contract.md`
