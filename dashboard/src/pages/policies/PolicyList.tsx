import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'

interface Policy {
    id: string
    name: string
}

export const PolicyList: React.FC = () => {
    const [policies, setPolicies] = useState<Policy[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.get('/policies')
            .then((data: any) => { setPolicies(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="policy-list">
            <h1>Policies</h1>
            <Link to="/policies/new/edit" className="btn-primary">Create Policy</Link>
            {policies.length === 0 ? (
                <p>No policies</p>
            ) : (
                <table>
                    <thead>
                        <tr><th>ID</th><th>Name</th><th>Actions</th></tr>
                    </thead>
                    <tbody>
                        {policies.map((policy) => (
                            <tr key={policy.id}>
                                <td>{policy.id}</td>
                                <td>{policy.name}</td>
                                <td>
                                    <Link to={`/policies/${policy.id}/edit`}>Edit</Link>
                                    <Link to={`/policies/${policy.id}/diff`}>Diff</Link>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    )
}
