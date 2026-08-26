import React, { useState } from 'react'
import { Dashboard } from './components/Dashboard'
import { login } from './api/client'

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async () => {
    setLoading(true)
    try {
      const data = await login(email, password)
      setToken(data.access_token)
      localStorage.setItem('token', data.access_token)
    } catch (error) {
      alert('Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    setToken('')
    localStorage.removeItem('token')
  }

  if (!token) {
    return (
      <div style={{ maxWidth: 400, margin: '50px auto', padding: 20, border: '1px solid #ccc', borderRadius: 8 }}>
        <h2>SentinelLayer</h2>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ width: '100%', marginBottom: 10, padding: 8 }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ width: '100%', marginBottom: 10, padding: 8 }}
        />
        <button
          onClick={handleLogin}
          disabled={loading}
          style={{ width: '100%', padding: 10, background: '#007bff', color: 'white', border: 'none', borderRadius: 4 }}
        >
          {loading ? 'Loading...' : 'Login'}
        </button>
        <p style={{ textAlign: 'center', marginTop: 10, fontSize: 12, color: '#999' }}>
          Default:  / 
        </p>
      </div>
    )
  }

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2>SentinelLayer Dashboard</h2>
        <button onClick={handleLogout} style={{ padding: '8px 16px', cursor: 'pointer' }}>Logout</button>
      </div>
      <Dashboard token={token} />
    </div>
  )
}

export default App
