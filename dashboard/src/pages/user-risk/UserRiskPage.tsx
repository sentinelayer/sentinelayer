import React, { useEffect, useState } from 'react'

export const UserRiskPage: React.FC = () => {
    const [users, setUsers] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/v1/user-risk')
            .then(res => res.json())
            .then(data => { setUsers(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="user-risk-page">
            <h1>User Risk</h1>
            <table>
                <thead>
                    <tr><th>User</th><th>Risk Score</th><th>Status</th><th>Last Activity</th></tr>
                </thead>
                <tbody>
                    {users.map((u: any, i: number) => (
                        <tr key={i}>
                            <td>{u.user_id || u.email || 'Unknown'}</td>
                            <td className={`risk-${u.risk_score > 70 ? 'high' : u.risk_score > 40 ? 'medium' : 'low'}`}>
                                {u.risk_score || 0}
                            </td>
                            <td>{u.status || 'Active'}</td>
                            <td>{u.last_activity || 'Never'}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}
