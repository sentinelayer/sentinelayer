# Applicability Engine

## Purpose
Determine which compliance frameworks apply to a customer based on:
- Customer type (enterprise, saas, fintech)
- Industry (finance, healthcare, government)
- Data type (PII, cardholder, health)
- Region (Indonesia, EU, US)

## Supported Frameworks
- SOC2
- ISO27001
- GDPR
- PCI DSS
- HIPAA

## Usage
POST /api/v1/compliance/applicability
{
  "customer_type": "enterprise",
  "industry": "fintech",
  "data_type": "cardholder",
  "region": "ID"
}

Response:
{
  "applicable_frameworks": ["PCI DSS", "SOC2", "GDPR"],
  "controls": [...]
}
