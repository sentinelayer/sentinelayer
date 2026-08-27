import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { apiGet } from '../../api/client'

type Version = { version: number; rules: Record<string, unknown>; active?: boolean }
type DiffResponse = { changed: boolean; diff: string; from_version: number; to_version: number }

export const PolicyDiff: React.FC = () => {
    const { id } = useParams()
    const [versions, setVersions] = useState<Version[]>([])
    const [fromVersion, setFromVersion] = useState(1)
    const [toVersion, setToVersion] = useState(1)
    const [diff, setDiff] = useState<DiffResponse | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!id) return
        apiGet<Version[]>(`/policies/${id}/versions`)
            .then((items) => {
                const ordered = [...items].sort((a, b) => a.version - b.version)
                setVersions(ordered)
                if (ordered.length > 1) {
                    setFromVersion(ordered[ordered.length - 2].version)
                    setToVersion(ordered[ordered.length - 1].version)
                } else if (ordered.length === 1) {
                    setFromVersion(ordered[0].version)
                    setToVersion(ordered[0].version)
                }
            })
            .catch(() => setError('Policy versions are not available'))
            .finally(() => setLoading(false))
    }, [id])

    useEffect(() => {
        if (!id || !versions.length) return
        apiGet<DiffResponse>(`/policies/${id}/diff?from_version=${fromVersion}&to_version=${toVersion}`)
            .then(setDiff)
            .catch(() => setDiff(null))
    }, [id, versions, fromVersion, toVersion])

    if (loading) return <div>Loading...</div>
    if (error) return <div className="error">{error}</div>
    if (!versions.length) return <div className="error">No policy versions available</div>

    return (
        <div className="policy-diff">
            <h1>Policy Diff</h1>
            <div>
                <label>From version</label>
                <select value={fromVersion} onChange={(e) => setFromVersion(Number(e.target.value))}>
                    {versions.map((v) => <option key={v.version} value={v.version}>Version {v.version}</option>)}
                </select>
                <label>To version</label>
                <select value={toVersion} onChange={(e) => setToVersion(Number(e.target.value))}>
                    {versions.map((v) => <option key={v.version} value={v.version}>Version {v.version}{v.active ? ' (active)' : ''}</option>)}
                </select>
            </div>
            {diff && (
                <div className="diff-container">
                    <p>{diff.changed ? 'Changes detected' : 'Versions are identical'}</p>
                    <pre>{diff.diff || '(no textual changes)'}</pre>
                </div>
            )}
        </div>
    )
}
