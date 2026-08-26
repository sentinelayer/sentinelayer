import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'

export const Login: React.FC = () => {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        try {
            const data = await api.post('/auth/login', { email, password })
            localStorage.setItem('token', data.access_token)
            localStorage.setItem('tenant_id', data.tenant_id || '')
            navigate('/')
        } catch (err) {
            setError('Invalid credentials')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="login-container">
            <h1>SentinelLayer</h1>
            <form onSubmit={handleSubmit}>
                {error && <div className="error">{error}</div>}
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
                <button type="submit" disabled={loading}>
                    {loading ? 'Loading...' : 'Login'}
                </button>
            </form>
        </div>
    )
}
