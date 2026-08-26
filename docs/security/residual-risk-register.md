# Residual Risk Register

## Risk: WAF bypass via obfuscation
- **Control**: Regex WAF
- **Residual Risk**: Medium
- **Acceptance**: Accepted for MVP
- **Mitigation**: Upgrade to Coraza in v0.2

## Risk: Tenant isolation bypass
- **Control**: RLS + TenantMiddleware
- **Residual Risk**: Low
- **Acceptance**: Accepted
- **Mitigation**: Regular pentest

## Risk: JWT secret exposure
- **Control**: Environment variable
- **Residual Risk**: Low
- **Acceptance**: Accepted
- **Mitigation**: KMS in v0.3

## Risk: Database injection
- **Control**: Parameterized queries
- **Residual Risk**: Low
- **Acceptance**: Accepted
