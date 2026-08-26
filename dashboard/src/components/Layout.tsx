import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { routes } from '../app/routes'

interface LayoutProps {
    children: React.ReactNode
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
    const navigate = useNavigate()

    const handleLogout = () => {
        localStorage.removeItem('token')
        localStorage.removeItem('tenant_id')
        navigate('/login')
    }

    return (
        <div className="layout" role="application" aria-label="SentinelLayer Dashboard">
            <nav className="sidebar" role="navigation" aria-label="Main navigation">
                <div className="logo" aria-label="SentinelLayer logo">SentinelLayer</div>
                <ul role="menubar">
                    <li role="none"><Link to={routes.overview} role="menuitem">Overview</Link></li>
                    <li role="none"><Link to={routes.events} role="menuitem">Events</Link></li>
                    <li role="none"><Link to={routes.alerts} role="menuitem">Alerts</Link></li>
                    <li role="none"><Link to={routes.incidents} role="menuitem">Incidents</Link></li>
                    <li role="none"><Link to={routes.evidence} role="menuitem">Evidence</Link></li>
                    <li role="none"><Link to={routes.risk} role="menuitem">Risk</Link></li>
                    <li role="none"><Link to="/attack-graph" role="menuitem">Attack Graph</Link></li>
                    <li role="none"><Link to="/heatmap" role="menuitem">Heatmap</Link></li>
                    <li role="none"><Link to="/user-risk" role="menuitem">User Risk</Link></li>
                    <li role="none"><Link to={routes.policies} role="menuitem">Policies</Link></li>
                    <li role="none"><Link to="/configuration" role="menuitem">Configuration</Link></li>
                    <li role="none"><Link to="/explainability" role="menuitem">Explainability</Link></li>
                    <li role="none"><Link to="/sla" role="menuitem">SLA</Link></li>
                    <li role="none"><Link to="/admin/break-glass" role="menuitem">Break Glass</Link></li>
                    <li role="none"><Link to="/admin/high-risk-actions" role="menuitem">High Risk</Link></li>
                </ul>
                <button onClick={handleLogout} className="logout-btn" aria-label="Logout">Logout</button>
            </nav>
            <main className="content" role="main">
                {children}
            </main>
        </div>
    )
}
