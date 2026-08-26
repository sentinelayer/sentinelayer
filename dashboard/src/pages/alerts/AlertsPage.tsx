import React, { useEffect, useState } from 'react'

export const AlertsPage: React.FC = () => {
    const [alerts, setAlerts] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/v1/alerts')
            .then(res => res.json())
            .then(data => { setAlerts(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="alerts-page">
            <h1>Alerts</h1>
            <table>
                <thead>
                    <tr><th>Severity</th><th>Message</th><th>Status</th><th>Time</th></tr>
                </thead>
                <tbody>
                    {alerts.map((a: any, i: number) => (
                        <tr key={i} className={`severity-${a.severity || 'low'}`}>
                            <td>{a.severity || 'Low'}</td>
                            <td>{a.message || 'Alert'}</td>
                            <td>{a.status || 'Active'}</td>
                            <td>{a.timestamp || 'Now'}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}
