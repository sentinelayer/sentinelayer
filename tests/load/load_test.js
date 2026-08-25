import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 0 },    // Ramp down to 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95% requests < 1s
    http_req_failed: ['rate<0.05'],    // <5% failures
  },
};

export default function () {
  // Login
  const loginRes = http.post('http://localhost:8000/api/v1/auth/login',
    JSON.stringify({ email: 'test@example.com', password: 'password123' }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  const token = loginRes.json('access_token');
  
  if (token) {
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };

    // Random endpoint
    const endpoints = [
      () => http.get('http://localhost:8000/api/v1/orders/', { headers }),
      () => http.post('http://localhost:8000/api/v1/orders/',
        JSON.stringify({
          product_id: 'prod-' + Math.random().toString(36).substring(7),
          quantity: Math.floor(Math.random() * 10) + 1,
          total_amount: Math.random() * 1000 + 100,
        }),
        { headers }
      ),
      () => http.get('http://localhost:8000/health'),
      () => http.get('http://localhost:8000/metrics'),
    ];

    const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
    const res = endpoint();
    
    check(res, {
      'status is 200 or 403': (r) => r.status === 200 || r.status === 403,
    });
  }

  sleep(Math.random() * 0.5 + 0.5);
}
