import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'

export const ExplainabilityPage: React.FC = () => {
    const [decision, setDecision] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.get('/explainability/latest')
            .then(data => {
                setDecision({
                    ...data,
                    what: `Decision was ${data.action}`,
                    why: data.reason || 'No explanation',
                    who: 'system',
                    when: data.timestamp || new Date().toISOString(),
                    signal: data.factors || {},
                    policy: data.policy || 'default',
                    version: data.version || '1.0'
                })
                setLoading(false)
            })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="explainability-page">
            <h1>Decision Explainability</h1>
            {decision ? (
                <div className="decision-detail">
                    <h2>WHAT</h2>
                    <p>{decision.what}</p>
                    <h2>WHY</h2>
                    <p>{decision.why}</p>
                    <h2>WHO</h2>
                    <p>{decision.who}</p>
                    <h2>WHEN</h2>
                    <p>{decision.when}</p>
                    <h2>SIGNAL</h2>
                    <ul>
                        {Object.entries(decision.signal).map(([k, v]) => (
                            <li key={k}>{k}: {String(v)}</li>
                        ))}
                    </ul>
                    <h2>SCORE</h2>
                    <p>{decision.risk_score}</p>
                    <h2>POLICY</h2>
                    <p>{decision.policy}</p>
                    <h2>VERSION</h2>
                    <p>{decision.version}</p>
                </div>
            ) : (
                <p>No decision data available</p>
            )}
        </div>
    )
}
