# Data Flows — SentinelLayer

## Primary Request Path (Data Plane)
Client -> TLS termination -> Gateway (Go reverse proxy) -> Coraza WAF + OWASP CRS -> Application Context normalization -> Behavior Engine -> Risk Engine -> Decision Safety Layer (fail-open/closed matrix) -> Upstream application OR block/monitor response

## Control Plane Path
Admin / Founder -> Auth (JWT + MFA gate) -> RBAC -> Gate Engine / Evidence / Policy APIs -> PostgreSQL (RLS)

## Telemetry Path
Data Plane + Control Plane -> structured logs (no secrets) -> metrics (Prometheus) -> traces. Integrity: clock skew <= 5s

## Evidence Path
Control / test / incident -> Evidence create (hash, version, owner) -> VERIFIED -> VALID -> linked to Requirement ID -> auto-EXPIRED on implementation version change
