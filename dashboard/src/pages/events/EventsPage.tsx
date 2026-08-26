import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'

export const EventsPage: React.FC = () => {
    const [events, setEvents] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    useEffect(() => {
        api.get('/events')
            .then(data => { setEvents(data); setLoading(false) })
            .catch(() => { setError('Failed to load events'); setLoading(false) })
    }, [])

    if (loading) return <div>Loading...</div>
    if (error) return <div className="error">{error}</div>

    return (
        <div className="events-page">
            <h1>Security Events</h1>
            {events.length === 0 ? (
                <p>No events yet</p>
            ) : (
                <table>
                    <thead>
                        <tr><th>Time</th><th>Type</th><th>Source</th><th>Data</th></tr>
                    </thead>
                    <tbody>
                        {events.map((e: any, i: number) => (
                            <tr key={i}>
                                <td>{e.timestamp || 'Now'}</td>
                                <td>{e.type || 'Unknown'}</td>
                                <td>{e.source || 'System'}</td>
                                <td>{JSON.stringify(e.data || {})}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    )
}
