import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { LoadingSkeleton } from '../../components/LoadingSkeleton'

type UserRisk = { user_id?: string; email?: string; risk_score?: number; status?: string; last_activity?: string }

export const UserRiskPage: React.FC = () => {
    const [users, setUsers] = useState<UserRisk[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const controller = new AbortController()
        api.get<UserRisk[]>('/user-risk', { signal: controller.signal })
            .then((data) => { if (!controller.signal.aborted) setUsers(Array.isArray(data) ? data : []) })
            .catch(() => undefined)
            .finally(() => { if (!controller.signal.aborted) setLoading(false) })
        return () => controller.abort()
    }, [])

    if (loading) return <LoadingSkeleton label="Loading user risk" />

    return (
        <div className="user-risk-page">
            <h1>User Risk</h1>
            {users.length === 0 ? (
                <p>No user risk data</p>
            ) : (
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
            )}
        </div>
    )
}

export default UserRiskPage;
