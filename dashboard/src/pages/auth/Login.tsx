import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export const Login: React.FC = () => {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const navigate = useNavigate()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            const res = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            })
            if (!res.ok) throw new Error('Login failed')
            const data = await res.json()
            localStorage.setItem('token', data.access_token)
            localStorage.setItem('tenant_id', data.tenant_id || '')
            navigate('/')
        } catch (e) {
            setError('Invalid credentials')
        }
    }

    return (
        <div className="login-container">
            <h1>SentinelLayer</h1>
            <form onSubmit={handleSubmit}>
                {error && <div className="error">{error}</div>}
                <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                <button type="submit">Login</button>
            </form>
        </div>
    )
}
