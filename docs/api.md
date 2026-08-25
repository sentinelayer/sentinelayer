# SentinelLayer API Documentation

## Base URL
Production: https://sentinelayer.up.railway.app
Development: http://localhost:8000

## Authentication
All endpoints require JWT token:
Authorization: Bearer <token>

## Endpoints

### Login
POST /api/v1/auth/login
Request: { "email": "test@example.com", "password": "password123" }
Response: { "access_token": "...", "token_type": "bearer", "expires_in": 900 }

### Orders
GET /api/v1/orders/ - List all orders
POST /api/v1/orders/ - Create order
GET /api/v1/orders/{id} - Get order by ID
PUT /api/v1/orders/{id} - Update order
DELETE /api/v1/orders/{id} - Delete order

### Risk
GET /api/v1/risk/calculate - Get risk score
POST /api/v1/risk/signal - Add risk signal

### Behavior
GET /api/v1/behavior/stats - Get behavior stats

### Decision
GET /api/v1/decision/stats - Get decision stats
POST /api/v1/decision/killswitch - Toggle kill switch

### Threat Intel
GET /api/v1/threatintel/ip/{ip} - Check IP reputation

### AI
POST /api/v1/ai/analyze - Analyze request with AI

### Control Plane
POST /api/v1/tenants - Create tenant
GET /api/v1/tenants - List tenants
POST /api/v1/applications - Create application
POST /api/v1/policies - Create policy

### Gate
GET /api/v1/gate/check/{requirement_id} - Check gate status

### Evidence
GET /api/v1/evidence/list - List evidence

### Keys
GET /api/v1/keys/status - Get key status
POST /api/v1/keys/rotate - Rotate keys

## Error Responses
{ "error": "message", "path": "/endpoint" }
