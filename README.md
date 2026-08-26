# SentinelLayer

API Security Platform — WAF + Behavioral Analysis + Risk Decision + Observability

SentinelLayer protects modern APIs from cyber attacks, business logic abuse, and data leaks. Built for solo founders, startups, and enterprises who need simple, affordable, and effective security.

---

## Architecture

Internet -> Gateway (WAF, Rate Limit, SSRF, Decision) -> Engine (Behavior, Risk, Decision, Threat Intel) -> Control Plane (Tenants, Policies, Incidents, Evidence) -> Dashboard (Overview, Events, Alerts, Incidents, Evidence, Risk)

---

## Features

Auth: JWT + bcrypt, MFA, RBAC, Break Glass Access
Security: WAF (CRS), Rate Limiting, SSRF Protection, Tenant Isolation, BOLA/IDOR Protection, Security Headers
Intelligence: Risk Engine, Behavior Engine, Threat Intelligence, AI Analysis
Decision: Circuit Breaker, Safe Mode, Monitor-Only Mode, Last Known Good
Observability: Prometheus Metrics, Distributed Tracing, Audit Log
Compliance: SOC2, ISO27001, GDPR (partial)
Operations: Incident Response, Evidence Collection, Offboarding Lifecycle, Disaster Recovery

---

## Quick Start

git clone https://github.com/sentinelayer/sentinelayer.git
cd sentinelayer
pip install -r requirements.txt
docker-compose -f infra/docker/docker-compose.yml up -d
alembic upgrade head
uvicorn control_plane.app.main:app --host 0.0.0.0 --port 8005
cd gateway && go run cmd/gateway/main.go

---

## Tech Stack

Gateway: Go + net/http
Control Plane: Python + FastAPI
Engine: Python
Dashboard: TypeScript + React
Database: PostgreSQL + SQLAlchemy
Cache: Redis
Monitoring: Prometheus + Grafana
Infrastructure: Docker + Kubernetes + Terraform

---

## Documentation

Architecture: docs/architecture/c4-context.md
Security: docs/security/threat-model-stride.md
Compliance: docs/compliance/uu-pdp.md
Runbooks: docs/runbooks/incident-response.md
API: docs/api/openapi-control-plane.yaml

---

## License

MIT (c) 2026 SentinelLayer
