# SentinelLayer

API Security Platform - WAF + Behavioral Analysis + Risk Decision + Observability

## Features

| Feature | Status | Note |
|---------|--------|------|
| JWT Authentication + bcrypt | YES | Production ready |
| WAF with OWASP-style rules | YES | 4+ rules active |
| Rate Limiting & Tenant Isolation | YES | Redis sliding window |
| Risk Scoring Engine | YES | Active |
| Circuit Breaker & Safe Mode | YES | Active |
| Threat Intelligence | YES | VirusTotal/AbuseIPDB |
| Observability | YES | Prometheus metrics |
| Compliance Reporting | PARTIAL | Partially implemented |
| Incident Response | PARTIAL | Partially implemented |
| GRC Evidence Collection | PARTIAL | Partially implemented |
| Security Dashboard | PARTIAL | Basic dashboard |

## Installation

pip install -r requirements.txt
alembic upgrade head
uvicorn src.sentinelayer.api.main:app --host 0.0.0.0 --port 8000

## License

MIT (c) 2026 SentinelLayer
