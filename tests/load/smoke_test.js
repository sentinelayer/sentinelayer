import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  // Test health endpoint
  const healthRes = http.get('http://localhost:8000/health');
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
  });

  // Login
  const loginPayload = JSON.stringify({
    email: 'test@example.com',
    password: 'password123',
  });
  const loginRes = http.post('http://localhost:8000/api/v1/auth/login', loginPayload, {
    headers: { 'Content-Type': 'application/json' },
  });
  check(loginRes, {
    'login status is 200': (r) => r.status === 200,
    'login response has token': (r) => r.json('access_token') !== undefined,
  });

  const token = loginRes.json('access_token');

  if (token) {
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };

    // Create order
    const orderPayload = JSON.stringify({
      product_id: 'prod-' + __VU,
      quantity: Math.floor(Math.random() * 10) + 1,
      total_amount: Math.random() * 1000 + 100,
    });
    const orderRes = http.post('http://localhost:8000/api/v1/orders/', orderPayload, { headers });
    check(orderRes, {
      'create order status is 200': (r) => r.status === 200,
    });

    // List orders
    const listRes = http.get('http://localhost:8000/api/v1/orders/', { headers });
    check(listRes, {
      'list orders status is 200': (r) => r.status === 200,
    });

    // Test WAF (should be blocked)
    const wafRes = http.get(
      'http://localhost:8000/api/v1/orders?search=SELECT%20*%20FROM%20users',
      { headers }
    );
    check(wafRes, {
      'WAF blocks SQL injection': (r) => r.status === 403,
    });
  }

  sleep(1);
}
