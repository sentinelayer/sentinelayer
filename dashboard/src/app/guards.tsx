import React, { useEffect } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

interface GuardsProps {
    children: React.ReactNode
}

export const Guards: React.FC<GuardsProps> = ({ children }) => {
    const token = localStorage.getItem('token')
    const navigate = useNavigate()

    useEffect(() => {
        if (!token) {
            navigate('/login')
        }
    }, [token, navigate])

    if (!token) {
        return <Navigate to="/login" replace />
    }

    return <>{children}</>
}
