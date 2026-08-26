import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'

export const RiskPage: React.FC = () => {
    const [risk, setRisk] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.get('/risk/calculate')
            .then(data => { setRisk(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="risk-page">
            <h1>Risk Score</h1>
            {risk ? (
                <div className="risk-detail">
                    <p><strong>Score:</strong> {risk.score}</p>
                    <p><strong>Confidence:</strong> {risk.confidence}</p>
                    <p><strong>Action:</strong> {risk.action}</p>
                    <div className="risk-factors">
                        <h3>Factors</h3>
                        {Object.entries(risk.factors || {}).map(([k, v]) => (
                            <div key={k}>{k}: {String(v)}</div>
                        ))}
                    </div>
                </div>
            ) : (
                <p>No risk data available</p>
            )}
        </div>
    )
}
