# SentinelLayer

API Security Platform — WAF + Behavioral Analysis + Risk Decision + Observability

SentinelLayer protects modern APIs from cyber attacks, business logic abuse, and data leaks. Built for solo founders, startups, and enterprises who need simple, affordable, and effective security.

---

## Architecture

Internet -> Gateway (WAF, Rate Limit, SSRF, Decision) -> Engine (Behavior, Risk, Decision, Threat Intel) -> Control Plane (Tenants, Policies, Incidents, Evidence) -> Dashboard (Overview, Events, Alerts, Incidents, Evidence, Risk)

---

## Features

| Feature | Status |
|---------|--------|
| JWT Authentication + bcrypt hashing | ✅ |
| WAF with OWASP-style rules | ✅ |
| Rate Limiting & Tenant Isolation | ✅ |
| Risk Scoring Engine | ✅ |
| Circuit Breaker & Safe Mode | ✅ |
| Threat Intelligence (VirusTotal/AbuseIPDB) | ✅ |
| Observability (Prometheus, Grafana, Tracing) | ✅ |
| Compliance Reporting (SOC2, ISO27001, GDPR) | 🟡 |
| Incident Response Automation | ✅ |
| GRC Evidence Collection | ✅ |
| Security Dashboard | ✅ |
| MFA | ✅ |
| RBAC | ✅ |
| Break Glass Access | ✅ |
| SSRF Protection | ✅ |
| BOLA/IDOR Protection | ✅ |
| AI Analysis (off-path) | ✅ |

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

Python + FastAPI
Go + net/http
PostgreSQL + Redis
React + TypeScript
Docker + Kubernetes + Terraform
Prometheus + Grafana

---

## About Me

Ex-Security Analyst:
- JPMorgan Chase
- Analyst Financial BEI
- Security Sinarmas
- Certified ETF

---

## Contact

GitHub: @sentinellayer
Email: muhamadivan969@gmail.com
LinkedIn: @sentinelayer
Twitter: @sentinelayer

---

## License

MIT (c) 2026 SentinelLayer
