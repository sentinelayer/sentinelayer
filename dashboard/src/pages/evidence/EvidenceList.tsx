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
        <div className="evidence-list">
            <h1>Evidence</h1>
            <table>
                <thead>
                    <tr><th>ID</th><th>Artifact</th><th>Status</th></tr>
                </thead>
                <tbody>
                    {evidence.map((e: any) => (
                        <tr key={e.id}>
                            <td>{e.id}</td>
                            <td>{e.artifact}</td>
                            <td>{e.status}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}
