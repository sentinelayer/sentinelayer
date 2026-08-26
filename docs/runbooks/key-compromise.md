# Key Compromise Runbook

## Detection
- Unauthorized access attempts
- Multiple invalid tokens
- Security alert from KMS

## Immediate Actions
1. Revoke compromised key
2. Rotate to new key
3. Re-sign active policies
4. Notify customers (if applicable)
5. Log all actions

## Recovery
1. All systems use new key
2. Old key revoked after overlap period
3. Post-incident review within 24 hours
4. Update key rotation policy
