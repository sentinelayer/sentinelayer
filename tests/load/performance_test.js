import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const wafBlocks = new Counter('waf_blocks');
const loginSuccess = new Rate('login_success');
const orderDuration = new Trend('order_duration');

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
    waf_blocks: ['count>10'],
    login_success: ['rate>0.95'],
    order_duration: ['p(95)<500'],
  },
};

export default function () {
  const startTime = Date.now();

  // 1. Health check (always allowed)
  const healthRes = http.get('http://localhost:8000/health');
  check(healthRes, {
    'health is 200': (r) => r.status === 200,
  });

  // 2. Login
  const loginStart = Date.now();
  const loginRes = http.post('http://localhost:8000/api/v1/auth/login',
    JSON.stringify({
      email: 'test@example.com',
      password: 'password123',
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  const loginOk = loginRes.status === 200 && loginRes.json('access_token');
  loginSuccess.add(loginOk);
  
  const token = loginRes.json('access_token');

  if (token) {
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };

    // 3. Create order
    const orderStart = Date.now();
    const orderRes = http.post('http://localhost:8000/api/v1/orders/',
      JSON.stringify({
        product_id: 'prod-' + Math.random().toString(36).substring(7),
        quantity: Math.floor(Math.random() * 10) + 1,
        total_amount: Math.round((Math.random() * 1000 + 100) * 100) / 100,
      }),
      { headers }
    );
    
    orderDuration.add(Date.now() - orderStart);
    check(orderRes, {
      'order created': (r) => r.status === 200,
    });

    // 4. List orders
    const listRes = http.get('http://localhost:8000/api/v1/orders/', { headers });
    check(listRes, {
      'orders listed': (r) => r.status === 200,
    });

    // 5. Test WAF (randomly)
    if (Math.random() < 0.1) {
      const attackTypes = [
        "SELECT%20*%20FROM%20users",
        "<script>alert(1)</script>",
        "../../../etc/passwd",
        "'; DROP TABLE orders; --",
      ];
      const attack = attackTypes[Math.floor(Math.random() * attackTypes.length)];
      
      const wafRes = http.get(
        `http://localhost:8000/api/v1/orders?search=${attack}`,
        { headers }
      );
      
      if (wafRes.status === 403) {
        wafBlocks.add(1);
      }
      
      check(wafRes, {
        'WAF blocks attack': (r) => r.status === 403,
      });
    }
  }

  // 6. Metrics endpoint (no auth)
  if (Math.random() < 0.05) {
    http.get('http://localhost:8000/metrics');
  }

  const totalDuration = Date.now() - startTime;
  sleep(Math.random() * 0.5 + 0.5);
}
