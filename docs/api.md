# SentinelLayer API Documentation

## Authentication
- POST /api/v1/auth/register
- POST /api/v1/auth/login

## Security
- GET /api/v1/risk/calculate
- POST /api/v1/decisions
- GET /api/v1/metrics/security

## Control Plane
- POST /api/v1/tenants
- GET /api/v1/tenants
- POST /api/v1/applications
- POST /api/v1/policies

## Observability
- GET /metrics
- GET /health
- GET /health/readiness
