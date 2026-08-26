# DR Restore Runbook

## Before Restore
- Confirm backup integrity
- Verify backup timestamp
- Prepare environment

## Restore Steps
1. Stop production traffic
2. Restore database from backup
3. Restore configuration
4. Verify data integrity
5. Test application health
6. Switch traffic back

## After Restore
- Verify all tenants accessible
- Check RPO/RTO compliance
- Log all actions
- Post-recovery review
