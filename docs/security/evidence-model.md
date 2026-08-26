# Evidence Model

## Schema
- **Evidence ID**: UUID
- **Requirement ID**: String
- **Control ID**: String
- **Artifact**: String (path or reference)
- **Hash**: SHA-256
- **Status**: CREATED → VERIFIED → VALID → EXPIRED/REVOKED
- **Created At**: Timestamp
- **Verified At**: Timestamp (optional)
- **Expires At**: Timestamp (optional)

## Lifecycle
1. CREATED - Evidence collected
2. VERIFIED - Hash verified
3. VALID - All checks pass
4. EXPIRED - Retention period exceeded
5. REVOKED - Implementation changed

## Retention
- 7 years for compliance evidence
- 30 days for operational evidence
- Configurable per type
