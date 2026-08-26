import React, { useEffect, useState } from 'react'

export const EvidenceList: React.FC = () => {
    const [evidence, setEvidence] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/v1/evidence')
            .then(res => res.json())
            .then(data => { setEvidence(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>
    return (
        <div>
            <h1>Evidence</h1>
            <ul>{evidence.map((e: any) => <li key={e.id}>{e.artifact} - {e.status}</li>)}</ul>
        </div>
    )
}
