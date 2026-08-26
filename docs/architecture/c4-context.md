# C4 Context — SentinelLayer

## System Context

Client (App/API) --HTTPS--> SentinelLayer (Data Plane + Control Plane)
SentinelLayer connects to: PostgreSQL (RLS), Redis (rate/cache), Observability (Prom/Loki)

## Actors
- Application / API client: sends requests through Data Plane (Gateway)
- Founder / Admin: manages policies, evidence, gates via Control Plane API
- External Retainer: read-only audit log + asynchronous dual-control approval
- Downstream service: receives only requests that passed Decision Safety Layer

## Trust Boundary
- Untrusted: Client network, public internet
- Semi-trusted: Data Plane (Gateway + WAF + Engines)
- Trusted: Control Plane, PostgreSQL (RLS), signed policy store
