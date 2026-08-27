import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'

export const PolicyEditor: React.FC = () => {
    const { id } = useParams()
    const navigate = useNavigate()
    const [name, setName] = useState('')
    const [rules, setRules] = useState('{}')
    const [version, setVersion] = useState(1)
    const [signature, setSignature] = useState('')
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (id) {
            api.get(`/policies/${id}`)
                .then((data: any) => {
                    setName(data.name || '')
                    setRules(JSON.stringify(data.rules || {}, null, 2))
                    setVersion(data.version || 1)
                    setSignature(data.signature || '')
                    setLoading(false)
                })
                .catch(() => setLoading(false))
        } else {
            setLoading(false)
        }
    }, [id])

    const handleSave = async () => {
        try {
            const data = await api.post('/policies', {
                name,
                rules: JSON.parse(rules),
                version: version + 1
            })
            navigate('/policies')
        } catch (e) {
            alert('Failed to save policy')
        }
    }

    if (loading) return <div>Loading...</div>

    return (
        <div className="policy-editor">
            <h1>{id ? 'Edit' : 'Create'} Policy</h1>
            <div>
                <label>Name</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
                <label>Version</label>
                <input type="number" value={version} readOnly />
            </div>
            <div>
                <label>Rules (JSON)</label>
                <textarea value={rules} onChange={(e) => setRules(e.target.value)} rows={10} />
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
