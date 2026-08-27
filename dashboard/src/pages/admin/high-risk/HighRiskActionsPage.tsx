import React, { useState } from 'react'
import { apiPost } from '../../../api/client'

export const HighRiskActionsPage: React.FC = () => {
    const [action, setAction] = useState('')
    const [reason, setReason] = useState('')
    const [result, setResult] = useState('')

    const handleExecute = async () => {
        if (!action || !reason.trim()) {
            setResult('Action and reason are required.')
            return
        }
        try {
            const data = await apiPost('/admin/high-risk-actions', { action, reason: reason.trim() })
            setResult(JSON.stringify(data, null, 2))
        } catch (error: any) {
            setResult('Error: ' + (error?.message || 'Request failed'))
        }
    }

    return (
        <div className="high-risk-actions-page">
            <h1>High Risk Actions</h1>
            <p>Warning: These actions require a separate approval and are recorded in the audit trail.</p>
            <div className="action-form">
                <select value={action} onChange={(e) => setAction(e.target.value)}>
                    <option value="">Select Action</option>
                    <option value="block_tenant">Block Tenant</option>
                    <option value="revoke_all_tokens">Revoke All Tokens</option>
                    <option value="disable_waf">Disable WAF</option>
                    <option value="force_rotation">Force Key Rotation</option>
                </select>
                <textarea placeholder="Reason for action" value={reason} onChange={(e) => setReason(e.target.value)} />
                <button onClick={handleExecute} disabled={!action || !reason.trim()}>Request Approval</button>
            </div>
            {result && <pre>{result}</pre>}
        </div>
    )
}

export default HighRiskActionsPage;
