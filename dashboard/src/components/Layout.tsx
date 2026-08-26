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
        <div className="layout">
            <nav className="sidebar">
                <div className="logo">SentinelLayer</div>
                <ul>
                    <li><Link to={routes.overview}>Overview</Link></li>
                    <li><Link to={routes.events}>Events</Link></li>
                    <li><Link to={routes.alerts}>Alerts</Link></li>
                    <li><Link to={routes.incidents}>Incidents</Link></li>
                    <li><Link to={routes.evidence}>Evidence</Link></li>
                    <li><Link to={routes.risk}>Risk</Link></li>
                    <li><Link to="/attack-graph">Attack Graph</Link></li>
                    <li><Link to="/heatmap">Heatmap</Link></li>
                    <li><Link to="/user-risk">User Risk</Link></li>
                    <li><Link to={routes.policies}>Policies</Link></li>
                    <li><Link to="/configuration">Configuration</Link></li>
                    <li><Link to="/explainability">Explainability</Link></li>
                    <li><Link to="/sla">SLA</Link></li>
                    <li><Link to="/admin/break-glass">Break Glass</Link></li>
                    <li><Link to="/admin/high-risk-actions">High Risk</Link></li>
                </ul>
                <button onClick={handleLogout} className="logout-btn">Logout</button>
            </nav>
            <main className="content">
                {children}
            </main>
        </div>
    )
}
