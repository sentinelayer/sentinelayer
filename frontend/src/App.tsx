import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [email, setEmail] = useState('test@example.com');
  const [password, setPassword] = useState('password123');
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState({ orders: 0, status: 'unknown' });

  const login = async () => {
    try {
      const res = await axios.post(`${API_URL}/api/v1/auth/login`, { email, password });
      setToken(res.data.access_token);
      localStorage.setItem('token', res.data.access_token);
    } catch (e) {
      alert('Login failed');
    }
  };

  const logout = () => {
    setToken('');
    localStorage.removeItem('token');
  };

  const fetchOrders = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/v1/orders/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOrders(res.data);
      setStats({ ...stats, orders: res.data.length });
    } catch (e) {
      console.error(e);
    }
  };

  const checkHealth = async () => {
    try {
      const res = await axios.get(`${API_URL}/health`);
      setStats({ ...stats, status: res.data.status });
    } catch (e) {
      setStats({ ...stats, status: 'unhealthy' });
    }
  };

  useEffect(() => {
    if (token) {
      fetchOrders();
      checkHealth();
    }
  }, [token]);

  if (!token) {
    return (
      <div style={{ maxWidth: 400, margin: '50px auto', padding: 20, border: '1px solid #ccc' }}>
        <h2>SentinelLayer</h2>
        <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: '100%', marginBottom: 10, padding: 8 }} />
        <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: '100%', marginBottom: 10, padding: 8 }} />
        <button onClick={login} style={{ width: '100%', padding: 10 }}>Login</button>
      </div>
    );
  }

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2>SentinelLayer Dashboard</h2>
        <button onClick={logout}>Logout</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, marginBottom: 20 }}>
        <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8 }}>
          <h3>Status</h3>
          <p>{stats.status === 'healthy' ? '✅ Healthy' : '❌ Unhealthy'}</p>
        </div>
        <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8 }}>
          <h3>Orders</h3>
          <p>{stats.orders}</p>
        </div>
        <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8 }}>
          <h3>Security</h3>
          <p>🛡️ Active</p>
        </div>
      </div>
      <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8 }}>
        <h3>Recent Orders</h3>
        <ul>
          {orders.slice(0, 5).map((o: any) => (
            <li key={o.id}>{o.id} - {o.product_id} - ${o.total_amount}</li>
          ))}
          {orders.length === 0 && <li>No orders</li>}
        </ul>
      </div>
    </div>
  );
}

export default App;
