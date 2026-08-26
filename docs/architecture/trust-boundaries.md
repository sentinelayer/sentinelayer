# Trust Boundaries

## Boundary 1: Internet → Gateway
- **Trust**: Untrusted
- **Controls**: WAF, Rate Limit, SSRF

## Boundary 2: Gateway → Engine
- **Trust**: Internal
- **Controls**: JWT, Tenant Isolation

## Boundary 3: Gateway → Upstream
- **Trust**: Semi-trusted
- **Controls**: JWT, Rate Limit

## Boundary 4: Control Plane → Database
- **Trust**: Internal
- **Controls**: RLS, Parameterized Queries

## Boundary 5: Dashboard → Control Plane
- **Trust**: Authenticated
- **Controls**: JWT, RBAC
