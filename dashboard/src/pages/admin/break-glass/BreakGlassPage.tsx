import React, { useEffect, useState } from 'react'
import { apiGet } from '../../../api/client'

export const BreakGlassPage: React.FC = () => {
    const [sessions, setSessions] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        apiGet<any[]>('/admin/breakglass')
            .then(setSessions)
            .catch(() => setError('Unable to load break-glass sessions'))
            .finally(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>
    if (error) return <div className="error">{error}</div>

    return (
        <div className="break-glass-page">
            <h1>Break Glass Sessions</h1>
            <table>
                <thead>
                    <tr><th>ID</th><th>User</th><th>Reason</th><th>Status</th><th>Expires</th></tr>
                </thead>
                <tbody>
                    {sessions.map((s) => (
                        <tr key={s.id}>
                            <td>{s.id}</td>
                            <td>{s.user_id}</td>
                            <td>{s.reason}</td>
                            <td>{s.status}</td>
                            <td>{s.expires_at}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

export default BreakGlassPage;
