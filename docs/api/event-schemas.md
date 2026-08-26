# Event Schemas

## RawRequest
{
  "method": "GET",
  "path": "/api/v1/orders",
  "headers": {"Authorization": "Bearer ..."},
  "body": null,
  "ip": "192.168.1.1"
}

## NormalizedRequest
{
  "method": "GET",
  "path": "/api/v1/orders",
  "tenant_id": "tenant-123",
  "user_id": "user-456",
  "ip": "192.168.1.1"
}

## SecurityEvent
{
  "type": "WAF_BLOCK",
  "tenant_id": "tenant-123",
  "timestamp": "2026-01-01T00:00:00Z",
  "data": {"rule_id": "SQLI-001", "payload": "' OR 1=1--"}
}

## RiskScore
{
  "tenant_id": "tenant-123",
  "score": 75,
  "confidence": 0.8,
  "factors": {"sql_injection": 30, "xss": 25, "rate_limit": 20},
  "timestamp": "2026-01-01T00:00:00Z"
}

## Decision
{
  "tenant_id": "tenant-123",
  "action": "BLOCK",
  "reason": "High risk score",
  "risk_score": 85,
  "timestamp": "2026-01-01T00:00:00Z"
}

## Incident
{
  "id": "inc-123",
  "tenant_id": "tenant-123",
  "severity": "HIGH",
  "description": "SQL injection attempt blocked",
  "status": "open",
  "created_at": "2026-01-01T00:00:00Z"
}
