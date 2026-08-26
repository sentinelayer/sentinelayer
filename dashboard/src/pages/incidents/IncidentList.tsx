import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'

export const IncidentList: React.FC = () => {
    const [incidents, setIncidents] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.get('/incidents')
            .then(data => { setIncidents(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="incident-list">
            <h1>Incidents</h1>
            {incidents.length === 0 ? (
                <p>No incidents</p>
            ) : (
                <table>
                    <thead>
                        <tr><th>ID</th><th>Severity</th><th>Description</th><th>Status</th></tr>
                    </thead>
                    <tbody>
                        {incidents.map((i: any) => (
                            <tr key={i.id}>
                                <td>{i.id}</td>
                                <td>{i.severity}</td>
                                <td>{i.description}</td>
                                <td>{i.status}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    )
}
