import React, { useEffect, useState } from 'react'

export const HeatmapPage: React.FC = () => {
    const [data, setData] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/v1/heatmap')
            .then(res => res.json())
            .then(data => { setData(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="heatmap-page">
            <h1>Risk Heatmap</h1>
            <div className="heatmap-container">
                <div className="heatmap-grid">
                    {data.length === 0 ? (
                        <p>No risk data available</p>
                    ) : (
                        <div className="heatmap-cells">
                            {data.map((cell: any, i: number) => (
                                <div key={i} className={`heatmap-cell risk-${cell.risk || 0}`}>
                                    {cell.endpoint || 'Unknown'}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
