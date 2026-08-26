import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

export const PolicyDiff: React.FC = () => {
    const { id } = useParams()
    const [v1, setV1] = useState<any>(null)
    const [v2, setV2] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        Promise.all([
            fetch(`/api/v1/policies/${id}/versions/1`).then(res => res.json()),
            fetch(`/api/v1/policies/${id}/versions/2`).then(res => res.json())
        ]).then(([d1, d2]) => {
            setV1(d1)
            setV2(d2)
            setLoading(false)
        }).catch(() => setLoading(false))
    }, [id])

    if (loading) return <div>Loading...</div>

    return (
        <div className="policy-diff">
            <h1>Policy Diff</h1>
            <div className="diff-container">
                <div className="diff-old">
                    <h3>Version 1</h3>
                    <pre>{JSON.stringify(v1, null, 2)}</pre>
                </div>
                <div className="diff-new">
                    <h3>Version 2</h3>
                    <pre>{JSON.stringify(v2, null, 2)}</pre>
                </div>
            </div>
        </div>
    )
}
