import React, { useState } from 'react'

export const HighRiskActionsPage: React.FC = () => {
    const [action, setAction] = useState('')
    const [reason, setReason] = useState('')
    const [result, setResult] = useState('')

    const handleExecute = () => {
        fetch('/api/v1/admin/high-risk-actions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, reason })
        })
            .then(res => res.json())
            .then(data => setResult(JSON.stringify(data, null, 2)))
            .catch(e => setResult('Error: ' + e.message))
    }

    return (
        <div className="high-risk-actions-page">
            <h1>High Risk Actions</h1>
            <p>Warning: These actions are irreversible and require approval</p>
            <div className="action-form">
                <select value={action} onChange={(e) => setAction(e.target.value)}>
                    <option value="">Select Action</option>
                    <option value="block_tenant">Block Tenant</option>
                    <option value="revoke_all_tokens">Revoke All Tokens</option>
                    <option value="disable_waf">Disable WAF</option>
                    <option value="force_rotation">Force Key Rotation</option>
                </select>
                <textarea placeholder="Reason for action" value={reason} onChange={(e) => setReason(e.target.value)} />
                <button onClick={handleExecute}>Execute (Requires Approval)</button>
            </div>
            {result && <pre>{result}</pre>}
        </div>
    )
}
