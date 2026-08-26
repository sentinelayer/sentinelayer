import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'

export const AlertsPage: React.FC = () => {
    const [alerts, setAlerts] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.get('/alerts')
            .then(data => { setAlerts(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="alerts-page">
            <h1>Alerts</h1>
            {alerts.length === 0 ? (
                <p>No alerts</p>
            ) : (
                <table>
                    <thead>
                        <tr><th>Severity</th><th>Message</th><th>Status</th></tr>
                    </thead>
                    <tbody>
                        {alerts.map((a: any, i: number) => (
                            <tr key={i}>
                                <td>{a.severity || 'Low'}</td>
                                <td>{a.message || 'Alert'}</td>
                                <td>{a.status || 'Active'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    )
}
