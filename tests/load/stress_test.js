import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 10 },
    { duration: '1m', target: 50 },
    { duration: '2m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '2m', target: 500 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.1'],
  },
};

export default function () {
  // Simple health check (no auth)
  const res = http.get('http://localhost:8000/health');
  check(res, {
    'health is 200': (r) => r.status === 200,
  });

  // Sometimes do authenticated requests
  if (Math.random() < 0.3) {
    const loginRes = http.post('http://localhost:8000/api/v1/auth/login',
      JSON.stringify({ email: 'test@example.com', password: 'password123' }),
      { headers: { 'Content-Type': 'application/json' } }
    );
    
    const token = loginRes.json('access_token');
    if (token) {
      http.get('http://localhost:8000/api/v1/orders/', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
    }
  }

  sleep(Math.random() * 0.2 + 0.1);
}
