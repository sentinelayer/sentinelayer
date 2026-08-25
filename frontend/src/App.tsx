import React, { useState, useEffect } from 'react';
import { login, getOrders, createOrder } from './api/client';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [email, setEmail] = useState('test@example.com');
  const [password, setPassword] = useState('password123');
  const [orders, setOrders] = useState([]);
  const [productId, setProductId] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [amount, setAmount] = useState(0);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    try {
      const data = await login(email, password);
      setToken(data.access_token);
      localStorage.setItem('token', data.access_token);
    } catch (e) {
      alert('Login failed');
    }
    setLoading(false);
  };

  const handleLogout = () => {
    setToken('');
    localStorage.removeItem('token');
  };

  const fetchOrders = async () => {
    if (!token) return;
    try {
      const data = await getOrders(token);
      setOrders(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateOrder = async () => {
    if (!token) return;
    setLoading(true);
    try {
      await createOrder(token, {
        product_id: productId || 'prod-123',
        quantity: quantity,
        total_amount: amount || 100.0,
      });
      fetchOrders();
      setProductId('');
      setQuantity(1);
      setAmount(0);
    } catch (e) {
      alert('Create order failed');
    }
    setLoading(false);
  };

  useEffect(() => {
    if (token) {
      fetchOrders();
    }
  }, [token]);

  if (!token) {
    return (
      <div style={{ maxWidth: 400, margin: '50px auto', padding: 20, border: '1px solid #ccc', borderRadius: 8 }}>
        <h2 style={{ textAlign: 'center' }}>SentinelLayer</h2>
        <p style={{ textAlign: 'center', color: '#666' }}>API Security Platform</p>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ width: '100%', marginBottom: 10, padding: 8, borderRadius: 4, border: '1px solid #ddd' }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ width: '100%', marginBottom: 10, padding: 8, borderRadius: 4, border: '1px solid #ddd' }}
        />
        <button
          onClick={handleLogin}
          disabled={loading}
          style={{ width: '100%', padding: 10, background: '#007bff', color: 'white', border: 'none', borderRadius: 4 }}
        >
          {loading ? 'Loading...' : 'Login'}
        </button>
        <p style={{ textAlign: 'center', marginTop: 10, fontSize: 12, color: '#999' }}>
          Default: test@example.com / password123
        </p>
      </div>
    );
  }

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2>SentinelLayer Dashboard</h2>
        <button onClick={handleLogout} style={{ padding: '8px 16px', cursor: 'pointer' }}>Logout</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, marginBottom: 20 }}>
        <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8 }}>
          <h3 style={{ margin: 0, color: '#666' }}>Total Orders</h3>
          <p style={{ fontSize: 24, fontWeight: 'bold', margin: 0 }}>{orders.length}</p>
        </div>
        <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8 }}>
          <h3 style={{ margin: 0, color: '#666' }}>Status</h3>
          <p style={{ fontSize: 24, fontWeight: 'bold', margin: 0, color: 'green' }}>✅ Healthy</p>
        </div>
        <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8 }}>
          <h3 style={{ margin: 0, color: '#666' }}>Security</h3>
          <p style={{ fontSize: 24, fontWeight: 'bold', margin: 0, color: 'green' }}>🛡️ Active</p>
        </div>
      </div>

      <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8, marginBottom: 20 }}>
        <h3 style={{ margin: '0 0 10px 0' }}>Create Order</h3>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Product ID"
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            style={{ padding: 8, borderRadius: 4, border: '1px solid #ddd' }}
          />
          <input
            type="number"
            placeholder="Quantity"
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
            style={{ padding: 8, borderRadius: 4, border: '1px solid #ddd', width: 80 }}
          />
          <input
            type="number"
            placeholder="Amount"
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            style={{ padding: 8, borderRadius: 4, border: '1px solid #ddd', width: 100 }}
          />
          <button
            onClick={handleCreateOrder}
            disabled={loading}
            style={{ padding: '8px 16px', background: '#28a745', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}
          >
            {loading ? 'Creating...' : 'Create'}
          </button>
        </div>
      </div>

      <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8 }}>
        <h3 style={{ margin: '0 0 10px 0' }}>Recent Orders</h3>
        {orders.length === 0 ? (
          <p>No orders found</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #ddd' }}>
                <th style={{ textAlign: 'left', padding: 8 }}>Product</th>
                <th style={{ textAlign: 'left', padding: 8 }}>Qty</th>
                <th style={{ textAlign: 'left', padding: 8 }}>Amount</th>
                <th style={{ textAlign: 'left', padding: 8 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.slice(0, 10).map((o: any) => (
                <tr key={o.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: 8 }}>{o.product_id}</td>
                  <td style={{ padding: 8 }}>{o.quantity}</td>
                  <td style={{ padding: 8 }}>${o.total_amount}</td>
                  <td style={{ padding: 8 }}>
                    <span style={{
                      background: o.status === 'pending' ? '#ffc107' : '#28a745',
                      color: 'white',
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: 12
                    }}>
                      {o.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default App;
