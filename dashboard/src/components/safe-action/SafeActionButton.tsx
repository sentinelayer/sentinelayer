import React, { useState } from 'react'

interface SafeActionButtonProps {
    action: string
    onConfirm: () => void
    children: React.ReactNode
    danger?: boolean
}

export const SafeActionButton: React.FC<SafeActionButtonProps> = ({
    action,
    onConfirm,
    children,
    danger = false
}) => {
    const [showConfirm, setShowConfirm] = useState(false)

    const handleClick = () => {
        if (danger) {
            setShowConfirm(true)
        } else {
            onConfirm()
        }
    }

    const handleConfirm = () => {
        setShowConfirm(false)
        onConfirm()
    }

    return (
        <div className="safe-action">
            {showConfirm ? (
                <div className="confirm-dialog">
                    <p>Are you sure you want to {action}?</p>
                    <div className="confirm-actions">
                        <button onClick={handleConfirm} className="confirm-yes">Yes</button>
                        <button onClick={() => setShowConfirm(false)} className="confirm-no">Cancel</button>
                    </div>
                </div>
            ) : (
                <button onClick={handleClick} className={danger ? 'danger' : ''}>
                    {children}
                </button>
            )}
        </div>
    )
}
