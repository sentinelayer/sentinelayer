import React, { useEffect, useState } from 'react'

interface Metric {
    name: string
    value: number
    status: string
}

export const OverviewPage: React.FC = () => {
    const [metrics, setMetrics] = useState<Metric[]>([])
    const [incidents, setIncidents] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        Promise.all([
            fetch('/api/v1/metrics/security').then(res => res.json()),
            fetch('/api/v1/incidents').then(res => res.json())
        ]).then(([metricsData, incidentsData]) => {
            setMetrics(metricsData)
            setIncidents(incidentsData)
            setLoading(false)
        }).catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="overview-page">
            <h1>Security Overview</h1>
            <div className="metrics-grid">
                {metrics.map((m) => (
                    <div key={m.name} className={`metric-card ${m.status}`}>
                        <h3>{m.name}</h3>
                        <p>{m.value}</p>
                    </div>
                ))}
            </div>
            <div className="incidents-section">
                <h2>Recent Incidents</h2>
                <ul>
                    {incidents.slice(0, 5).map((i: any) => (
                        <li key={i.id}>{i.severity} - {i.description}</li>
                    ))}
                </ul>
            </div>
        </div>
    )
}
