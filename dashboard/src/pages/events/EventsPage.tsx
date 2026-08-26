import React, { useEffect, useState } from 'react'

export const EventsPage: React.FC = () => {
    const [events, setEvents] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/v1/events')
            .then(res => res.json())
            .then(data => { setEvents(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="events-page">
            <h1>Security Events</h1>
            <table>
                <thead>
                    <tr><th>Time</th><th>Type</th><th>Tenant</th><th>Source</th><th>Action</th></tr>
                </thead>
                <tbody>
                    {events.map((e: any, i: number) => (
                        <tr key={i}>
                            <td>{e.timestamp || 'Now'}</td>
                            <td>{e.type || 'Unknown'}</td>
                            <td>{e.tenant_id || '-'}</td>
                            <td>{e.source || 'System'}</td>
                            <td>{e.action || 'Allow'}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}
