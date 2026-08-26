import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Login } from '../pages/auth/Login'
import { OverviewPage } from '../pages/overview/OverviewPage'
import { EventsPage } from '../pages/events/EventsPage'
import { AlertsPage } from '../pages/alerts/AlertsPage'
import { IncidentList } from '../pages/incidents/IncidentList'
import { EvidenceList } from '../pages/evidence/EvidenceList'
import { RiskPage } from '../pages/risk/RiskPage'
import { AttackGraphPage } from '../pages/attack-graph/AttackGraphPage'
import { HeatmapPage } from '../pages/heatmap/HeatmapPage'
import { UserRiskPage } from '../pages/user-risk/UserRiskPage'
import { PolicyList } from '../pages/policies/PolicyList'
import { PolicyEditor } from '../pages/policies/PolicyEditor'
import { PolicyDiff } from '../pages/policies/PolicyDiff'
import { ConfigurationPage } from '../pages/configuration/ConfigurationPage'
import { ExplainabilityPage } from '../pages/explainability/ExplainabilityPage'
import { BreakGlassPage } from '../pages/admin/break-glass/BreakGlassPage'
import { HighRiskActionsPage } from '../pages/admin/high-risk/HighRiskActionsPage'
import { SLAPage } from '../pages/sla/SLAPage'
import { Guards } from './guards'

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/" element={<Guards><OverviewPage /></Guards>} />
                <Route path="/events" element={<Guards><EventsPage /></Guards>} />
                <Route path="/alerts" element={<Guards><AlertsPage /></Guards>} />
                <Route path="/incidents" element={<Guards><IncidentList /></Guards>} />
                <Route path="/evidence" element={<Guards><EvidenceList /></Guards>} />
                <Route path="/risk" element={<Guards><RiskPage /></Guards>} />
                <Route path="/attack-graph" element={<Guards><AttackGraphPage /></Guards>} />
                <Route path="/heatmap" element={<Guards><HeatmapPage /></Guards>} />
                <Route path="/user-risk" element={<Guards><UserRiskPage /></Guards>} />
                <Route path="/policies" element={<Guards><PolicyList /></Guards>} />
                <Route path="/policies/:id/edit" element={<Guards><PolicyEditor /></Guards>} />
                <Route path="/policies/:id/diff" element={<Guards><PolicyDiff /></Guards>} />
                <Route path="/configuration" element={<Guards><ConfigurationPage /></Guards>} />
                <Route path="/explainability" element={<Guards><ExplainabilityPage /></Guards>} />
                <Route path="/admin/break-glass" element={<Guards><BreakGlassPage /></Guards>} />
                <Route path="/admin/high-risk-actions" element={<Guards><HighRiskActionsPage /></Guards>} />
                <Route path="/sla" element={<Guards><SLAPage /></Guards>} />
            </Routes>
        </BrowserRouter>
    )
}

export default App
