import React from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { routes } from '../app/routes'
import { logout } from '../api/client'

interface LayoutProps {
  children: React.ReactNode
}

const NAV: { to: string; label: string }[] = [
  { to: routes.overview, label: 'Overview' },
  { to: '/applications', label: 'Applications' },
  { to: routes.events, label: 'Events' },
  { to: routes.alerts, label: 'Alerts' },
  { to: routes.incidents, label: 'Incidents' },
  { to: routes.evidence, label: 'Evidence' },
  { to: routes.risk, label: 'Risk' },
  { to: '/attack-graph', label: 'Attack Graph' },
  { to: '/heatmap', label: 'Heatmap' },
  { to: '/user-risk', label: 'User Risk' },
  { to: routes.policies, label: 'Policies' },
  { to: '/configuration', label: 'Configuration' },
  { to: '/explainability', label: 'Explainability' },
  { to: '/sla', label: 'SLA' },
  { to: '/admin/break-glass', label: 'Break Glass' },
  { to: '/admin/high-risk-actions', label: 'High Risk' },
]

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="layout" style={{ display: 'flex', minHeight: '100vh', background: '#0a0a0a', color: '#e8e8e8', fontFamily: 'system-ui,sans-serif' }}>
      <nav style={{ width: 220, borderRight: '1px solid #333', padding: 16, flexShrink: 0 }}>
        <div style={{ color: '#00ff88', fontWeight: 700, marginBottom: 16 }}>SentinelLayer</div>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {NAV.map((item) => (
            <li key={item.to} style={{ marginBottom: 6 }}>
              <Link
                to={item.to}
                style={{
                  color: location.pathname === item.to ? '#00ff88' : '#ccc',
                  textDecoration: 'none',
                  fontWeight: location.pathname === item.to ? 600 : 400,
                }}
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
        <button
          onClick={handleLogout}
          style={{ marginTop: 24, background: '#331111', color: '#ff8888', border: '1px solid #553333', padding: '8px 12px', cursor: 'pointer', borderRadius: 4, width: '100%' }}
        >
          Logout
        </button>
      </nav>
      <main style={{ flex: 1, padding: 20 }}>{children}</main>
    </div>
  )
}
