import React from 'react'
import { apiPost } from '../../api/client'
import { SafeActionButton } from './SafeActionButton'

interface MassBlockButtonProps {
    tenantId: string
    onBlock: () => void
}

export const MassBlockButton: React.FC<MassBlockButtonProps> = ({ tenantId, onBlock }) => {
    const handleBlock = async () => {
        try {
            await apiPost('/admin/high-risk-actions', {
                action: 'block_tenant',
                reason: `Mass block for tenant ${tenantId}`,
            })
            onBlock()
        } catch {
            // The parent can refresh the action state; no destructive action is applied on failure.
        }
    }

    return (
        <SafeActionButton
            action="block all traffic"
            onConfirm={handleBlock}
            danger={true}
        >
            Block All Traffic
        </SafeActionButton>
    )
}
