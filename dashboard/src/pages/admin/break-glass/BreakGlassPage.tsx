import React, { useEffect, useState } from 'react'

export const BreakGlassPage: React.FC = () => {
    const [sessions, setSessions] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/v1/admin/breakglass')
            .then(res => res.json())
            .then((data: any) => { setSessions(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="break-glass-page">
            <h1>Break Glass Sessions</h1>
            <table>
                <thead>
                    <tr><th>ID</th><th>User</th><th>Reason</th><th>Status</th><th>Expires</th></tr>
                </thead>
                <tbody>
                    {sessions.map((s: any) => (
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
