import React, { useEffect, useState } from 'react'

export const RiskPage: React.FC = () => {
    const [risk, setRisk] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/v1/risk/calculate')
            .then(res => res.json())
            .then(data => { setRisk(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="risk-page">
            <h1>Risk Score</h1>
            {risk && (
                <div className="risk-detail">
                    <p>Score: {risk.score}</p>
                    <p>Confidence: {risk.confidence}</p>
                    <p>Action: {risk.action}</p>
                    <div className="risk-factors">
                        <h3>Factors</h3>
                        {Object.entries(risk.factors || {}).map(([k, v]) => (
                            <div key={k}>{k}: {String(v)}</div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
