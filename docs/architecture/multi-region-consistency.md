# Multi-Region Consistency Model

## Policy Monotonicity
- All policies are timestamped
- Newer version overwrites older version
- Version ordering maintained

## Signature Verification
- Every policy version is signed
- Signature must match public key
- Invalid signatures are rejected

## Cross-Region Convergence
- Last-known-good policy used when divergence > 5 minutes
- Audit log tracks all changes
- Alert on divergence > 10 minutes

## Security-Critical Policy
- Divergence > 5% triggers alert
- Emergency rollback available
- All changes logged
