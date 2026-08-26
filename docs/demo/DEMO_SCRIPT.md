# SentinelLayer Demo Script

## 1. Login (0:00-0:30)
- Buka Swagger UI
- POST /api/v1/auth/login
- Dapat token

## 2. Create Order (0:30-1:00)
- POST /api/v1/orders/
- Body: {"product_id":"prod-123","quantity":2,"total_amount":100.0}
- Response: order created

## 3. List Orders (1:00-1:30)
- GET /api/v1/orders/
- Lihat semua orders

## 4. WAF Protection (1:30-2:00)
- GET /api/v1/orders?search=SELECT * FROM users
- Response: 403 Blocked by WAF

## 5. Dashboard (2:00-2:30)
- Buka frontend
- Login
- Lihat stats
