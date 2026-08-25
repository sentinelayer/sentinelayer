import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 20 },
    { duration: '3m', target: 50 },
    { duration: '2m', target: 100 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.02'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // Login
  const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
    email: 'test@example.com',
    password: 'password123'
  }), { headers: { 'Content-Type': 'application/json' } });
  
  const token = loginRes.json('access_token');
  
  if (token) {
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
    
    // Health check
    http.get(`${BASE_URL}/health`);
    
    // List orders
    http.get(`${BASE_URL}/api/v1/orders/`, { headers });
    
    // Create order (randomly)
    if (Math.random() < 0.3) {
      http.post(`${BASE_URL}/api/v1/orders/`, JSON.stringify({
        product_id: 'prod-' + Math.random().toString(36).substring(7),
        quantity: Math.floor(Math.random() * 10) + 1,
        total_amount: Math.random() * 1000 + 100,
      }), { headers });
    }
  }
  
  sleep(Math.random() * 0.5 + 0.5);
}
