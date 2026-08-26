import React, { useState } from 'react'
import { SafeActionButton } from './SafeActionButton'

interface MassBlockButtonProps {
    tenantId: string
    onBlock: () => void
}

export const MassBlockButton: React.FC<MassBlockButtonProps> = ({ tenantId, onBlock }) => {
    const handleBlock = () => {
        fetch('/api/v1/admin/high-risk-actions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'mass_block',
                reason: `Mass block for tenant ${tenantId}`
            })
        }).then(() => onBlock())
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
