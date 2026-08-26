# SentinelLayer

API Security Platform - WAF + Behavioral Analysis + Risk Decision + Observability

## Features

| Feature | Status |
|---------|--------|
| JWT Authentication + bcrypt | YES |
| WAF with OWASP-style rules | YES |
| Rate Limiting & Tenant Isolation | YES |
| Risk Scoring Engine | YES |
| Circuit Breaker & Safe Mode | YES |
| Threat Intelligence | YES |
| Observability | YES |
| Compliance Reporting | YES |
| Incident Response | YES |
| GRC Evidence Collection | YES |
| Security Dashboard | YES |

## Installation

pip install -r requirements.txt
alembic upgrade head
uvicorn src.sentinelayer.api.main_full:app --host 0.0.0.0 --port 8000

## License

MIT (c) 2026 SentinelLayer
