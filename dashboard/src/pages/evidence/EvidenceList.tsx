import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'

export const EvidenceList: React.FC = () => {
    const [evidence, setEvidence] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.get('/evidence')
            .then((data: any) => { setEvidence(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="evidence-list">
            <h1>Evidence</h1>
            {evidence.length === 0 ? (
                <p>No evidence</p>
            ) : (
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
            )}
        </div>
    )
}

export default EvidenceList;
