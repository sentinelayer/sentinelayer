import React, { useEffect, useState } from 'react'

export const ExplainabilityPage: React.FC = () => {
    const [decision, setDecision] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/v1/explainability/latest')
            .then(res => res.json())
            .then(data => { setDecision(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="explainability-page">
            <h1>Decision Explainability</h1>
            {decision ? (
                <div className="decision-detail">
                    <p><strong>Action:</strong> {decision.action}</p>
                    <p><strong>Risk Score:</strong> {decision.risk_score}</p>
                    <p><strong>Reason:</strong> {decision.reason || 'No explanation'}</p>
                    <div className="decision-factors">
                        <h3>Factors</h3>
                        {Object.entries(decision.factors || {}).map(([k, v]) => (
                            <div key={k}>{k}: {String(v)}</div>
                        ))}
                    </div>
                </div>
            ) : (
                <p>No decision data available</p>
            )}
        </div>
    )
}
