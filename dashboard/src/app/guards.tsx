import React from 'react'
import { Navigate } from 'react-router-dom'

interface GuardsProps {
  children: React.ReactNode
}

export const Guards: React.FC<GuardsProps> = ({ children }) => {
  const token = localStorage.getItem('token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}
