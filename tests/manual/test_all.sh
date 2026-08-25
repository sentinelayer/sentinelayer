#!/bin/bash
# Manual test script untuk semua endpoints

echo "🔍 Testing SentinelLayer API..."
echo "================================"

# Health check
echo "1. Health check:"
curl -s http://localhost:8000/health | jq .
echo ""

# Root
echo "2. Root endpoint:"
curl -s http://localhost:8000/ | jq .
echo ""

# Login
echo "3. Login:"
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' \
  | jq -r '.access_token')
echo "   Token: ${TOKEN:0:50}..."
echo ""

# Create order
echo "4. Create order:"
ORDER=$(curl -s -X POST http://localhost:8000/api/v1/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id":"prod-123","quantity":2,"total_amount":100.0}' \
  | jq '.')
echo "$ORDER" | jq .
ORDER_ID=$(echo "$ORDER" | jq -r '.id')
echo ""

# List orders
echo "5. List orders:"
curl -s -X GET http://localhost:8000/api/v1/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
echo ""

# Get order
echo "6. Get order $ORDER_ID:"
curl -s -X GET http://localhost:8000/api/v1/orders/$ORDER_ID \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
echo ""

# Test WAF - SQL Injection
echo "7. Test WAF (SQL Injection):"
curl -s -X GET "http://localhost:8000/api/v1/orders?search=SELECT%20*%20FROM%20users" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nStatus: %{http_code}\n"
echo ""

# Test WAF - XSS
echo "8. Test WAF (XSS):"
curl -s -X GET "http://localhost:8000/api/v1/orders?q=<script>alert(1)</script>" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nStatus: %{http_code}\n"
echo ""

# Metrics
echo "9. Metrics:"
curl -s http://localhost:8000/metrics | grep -E "^sentinelayer_(requests|waf|rate|auth)" | head -10
echo ""

echo "✅ All tests completed!"
