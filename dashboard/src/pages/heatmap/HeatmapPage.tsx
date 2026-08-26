import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'

export const HeatmapPage: React.FC = () => {
    const [data, setData] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.get('/heatmap')
            .then(data => { setData(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="heatmap-page">
            <h1>Risk Heatmap</h1>
            {data.length === 0 ? (
                <p>No risk data available</p>
            ) : (
                <div className="heatmap-grid">
                    {data.map((cell: any, i: number) => (
                        <div key={i} className={`heatmap-cell risk-${cell.risk || 0}`}>
                            {cell.endpoint || 'Unknown'}
                            <span className="heatmap-value">{cell.risk || 0}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
