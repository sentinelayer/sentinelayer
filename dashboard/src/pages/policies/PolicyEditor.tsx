import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

export const PolicyEditor: React.FC = () => {
    const { id } = useParams()
    const navigate = useNavigate()
    const [name, setName] = useState('')
    const [rules, setRules] = useState('{}')
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (id) {
            fetch(`/api/v1/policies/${id}`)
                .then(res => res.json())
                .then(data => {
                    setName(data.name || '')
                    setRules(JSON.stringify(data.rules || {}, null, 2))
                    setLoading(false)
                })
                .catch(() => setLoading(false))
        } else {
            setLoading(false)
        }
    }, [id])

    const handleSave = () => {
        const method = id ? 'PUT' : 'POST'
        const url = id ? `/api/v1/policies/${id}` : '/api/v1/policies'
        fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, rules: JSON.parse(rules) })
        }).then(() => navigate('/policies'))
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
                <label>Rules (JSON)</label>
                <textarea value={rules} onChange={(e) => setRules(e.target.value)} rows={10} />
            </div>
            <button onClick={handleSave}>Save</button>
        </div>
    )
}
