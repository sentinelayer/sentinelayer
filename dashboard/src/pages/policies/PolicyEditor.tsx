import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'

export const PolicyEditor: React.FC = () => {
    const { id } = useParams()
    const navigate = useNavigate()
    const [name, setName] = useState('')
    const [rules, setRules] = useState('{}')
    const [version, setVersion] = useState(0)
    const [signature, setSignature] = useState('')
    const [loading, setLoading] = useState(Boolean(id))
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!id) return
        api.get(`/policies/${id}`)
            .then((data: any) => {
                setName(data.name || '')
                setRules(JSON.stringify(data.rules || {}, null, 2))
                setVersion(data.version || 1)
                setSignature(data.signature || '')
            })
            .catch(() => setError('Failed to load policy'))
            .finally(() => setLoading(false))
    }, [id])

    const handleSave = async () => {
        setError(null)
        try {
            const parsedRules = JSON.parse(rules)
            if (id) {
                await api.post(`/policies/${id}/versions`, { name, rules: parsedRules })
            } else {
                await api.post('/policies', { name, rules: parsedRules })
            }
            navigate('/policies')
        } catch (e) {
            setError(e instanceof SyntaxError ? 'Rules must be valid JSON' : 'Failed to save policy')
        }
    }

    if (loading) return <div>Loading...</div>

    return (
        <div className="policy-editor">
            <h1>{id ? 'Edit' : 'Create'} Policy</h1>
            {error && <p className="error">{error}</p>}
            <div>
                <label>Name</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div>
                <label>Version</label>
                <input type="number" value={version || 1} readOnly />
            </div>
            <div>
                <label>Rules (JSON)</label>
                <textarea value={rules} onChange={(e) => setRules(e.target.value)} rows={10} required />
            </div>
            {signature && (
                <div>
                    <label>Signature</label>
                    <input type="text" value={signature} readOnly />
                </div>
            )}
            <button onClick={handleSave}>Save</button>
        </div>
    )
}
