import React, { useState, useEffect } from 'react'
import axios from 'axios'

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000'

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [orders, setOrders] = useState([])
  const [security, setSecurity] = useState({ waf: 'active', rate_limit: 'active' })

  const login = async () => {
    try {
      const res = await axios.post(`${API}/api/v1/auth/login`, { email, password })
      setToken(res.data.access_token)
      localStorage.setItem('token', res.data.access_token)
    } catch {
      alert('Login failed')
    }
  }

  const logout = () => {
    setToken('')
    localStorage.removeItem('token')
  }

  useEffect(() => {
    if (!token) return
    const fetch = async () => {
      try {
        const o = await axios.get(`${API}/api/v1/orders/`, { headers: { Authorization: `Bearer ${token}` } })
        setOrders(o.data)
        const s = await axios.get(`${API}/api/v1/dashboard/security`, { headers: { Authorization: `Bearer ${token}` } })
        setSecurity(s.data)
      } catch {}
    }
    fetch()
  }, [token])

  if (!token) {
    return (
      <div style={{ maxWidth: 400, margin: '50px auto', padding: 20, border: '1px solid #ccc' }}>
        <h2>SentinelLayer</h2>
        <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} style={{ width: '100%', marginBottom: 10, padding: 8 }} />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} style={{ width: '100%', marginBottom: 10, padding: 8 }} />
        <button onClick={login} style={{ width: '100%', padding: 10 }}>Login</button>
      </div>
    )
  }

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h2>SentinelLayer Dashboard</h2>
        <button onClick={logout}>Logout</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 20, margin: '20px 0' }}>
        <div style={{ border: '1px solid #ccc', padding: 20 }}><h3>WAF</h3><p>{security.waf === 'active' ? '✅ Active' : '❌ Inactive'}</p></div>
        <div style={{ border: '1px solid #ccc', padding: 20 }}><h3>Rate Limit</h3><p>{security.rate_limit === 'active' ? '✅ Active' : '❌ Inactive'}</p></div>
        <div style={{ border: '1px solid #ccc', padding: 20 }}><h3>Orders</h3><p>{orders.length}</p></div>
      </div>
      <div style={{ border: '1px solid #ccc', padding: 20 }}>
        <h3>Recent Orders</h3>
        <ul>
          {orders.slice(0, 10).map((o: any) => <li key={o.id}>{o.product_id} - {o.quantity}x - ${o.total_amount}</li>)}
        </ul>
      </div>
    </div>
  )
}

export default App
