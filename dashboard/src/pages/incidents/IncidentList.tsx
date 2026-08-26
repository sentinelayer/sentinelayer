import React, { useEffect, useState } from 'react'

export const IncidentList: React.FC = () => {
    const [incidents, setIncidents] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/v1/incidents')
            .then(res => res.json())
            .then(data => { setIncidents(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>
    return (
        <div>
            <h1>Incidents</h1>
            <ul>{incidents.map((i: any) => <li key={i.id}>{i.severity} - {i.status}</li>)}</ul>
        </div>
    )
}
