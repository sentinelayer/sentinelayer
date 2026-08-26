# Policy Rollback Runbook

## When to Rollback
- Policy causing false positives
- Policy blocking legitimate traffic
- Customer complaints
- Security incident from policy

## Rollback Steps
1. Identify policy version to rollback to
2. Verify version signature
3. Apply rollback
4. Test with sample traffic
5. Monitor for 1 hour
6. Log all actions

## Validation
- Policy version signed
- Last-known-good verified
- Tenant isolation maintained
