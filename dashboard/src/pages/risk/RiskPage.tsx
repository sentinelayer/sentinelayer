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
        <div>
            <h1>Risk Score</h1>
            {risk && <p>Score: {risk.score}</p>}
        </div>
    )
}
