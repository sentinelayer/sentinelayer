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

  const handleLogin = async () => {
    try {
      const data = await login(email, password);
      setToken(data.access_token);
      localStorage.setItem('token', data.access_token);
    } catch (e) {
      alert('Login failed');
    }
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
    try {
      await createOrder(token, {
        product_id: productId || 'prod-123',
        quantity: quantity,
        total_amount: amount || 100.0,
      });
      fetchOrders();
    } catch (e) {
      alert('Create order failed');
    }
  };

  useEffect(() => {
    if (token) {
      fetchOrders();
    }
  }, [token]);

  if (!token) {
    return (
      <div style={{ maxWidth: 400, margin: '50px auto', padding: 20, border: '1px solid #ccc', borderRadius: 8 }}>
        <h2>SentinelLayer</h2>
        <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: '100%', marginBottom: 10, padding: 8 }} />
        <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: '100%', marginBottom: 10, padding: 8 }} />
        <button onClick={handleLogin} style={{ width: '100%', padding: 10 }}>Login</button>
      </div>
    );
  }

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>SentinelLayer Dashboard</h2>
        <button onClick={handleLogout}>Logout</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, margin: '20px 0' }}>
        <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8 }}>
          <h3>Orders</h3>
          <p>{orders.length}</p>
        </div>
        <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8 }}>
          <h3>Status</h3>
          <p>✅ Healthy</p>
        </div>
        <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8 }}>
          <h3>Security</h3>
          <p>🛡️ Active</p>
        </div>
      </div>
      <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8, marginBottom: 20 }}>
        <h3>Create Order</h3>
        <input type="text" placeholder="Product ID" value={productId} onChange={(e) => setProductId(e.target.value)} style={{ marginRight: 10, padding: 8 }} />
        <input type="number" placeholder="Qty" value={quantity} onChange={(e) => setQuantity(Number(e.target.value))} style={{ marginRight: 10, padding: 8, width: 60 }} />
        <input type="number" placeholder="Amount" value={amount} onChange={(e) => setAmount(Number(e.target.value))} style={{ marginRight: 10, padding: 8, width: 100 }} />
        <button onClick={handleCreateOrder}>Create</button>
      </div>
      <div style={{ border: '1px solid #ccc', padding: 20, borderRadius: 8 }}>
        <h3>Recent Orders</h3>
        <ul>
          {orders.slice(0, 10).map((o: any) => (
            <li key={o.id}>{o.product_id} - {o.quantity}x - ${o.total_amount} ({o.status})</li>
          ))}
          {orders.length === 0 && <li>No orders</li>}
        </ul>
      </div>
    </div>
  );
}

export default App;
