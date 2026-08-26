import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Login } from '../pages/auth/Login'
import { Guards } from './guards'
import { Layout } from '../components/Layout'
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

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/*" element={
                    <Guards>
                        <Layout>
                            <Routes>
                                <Route path="/" element={<OverviewPage />} />
                                <Route path="/events" element={<EventsPage />} />
                                <Route path="/alerts" element={<AlertsPage />} />
                                <Route path="/incidents" element={<IncidentList />} />
                                <Route path="/evidence" element={<EvidenceList />} />
                                <Route path="/risk" element={<RiskPage />} />
                                <Route path="/attack-graph" element={<AttackGraphPage />} />
                                <Route path="/heatmap" element={<HeatmapPage />} />
                                <Route path="/user-risk" element={<UserRiskPage />} />
                                <Route path="/policies" element={<PolicyList />} />
                                <Route path="/policies/:id/edit" element={<PolicyEditor />} />
                                <Route path="/policies/:id/diff" element={<PolicyDiff />} />
                                <Route path="/configuration" element={<ConfigurationPage />} />
                                <Route path="/explainability" element={<ExplainabilityPage />} />
                                <Route path="/admin/break-glass" element={<BreakGlassPage />} />
                                <Route path="/admin/high-risk-actions" element={<HighRiskActionsPage />} />
                                <Route path="/sla" element={<SLAPage />} />
                            </Routes>
                        </Layout>
                    </Guards>
                } />
            </Routes>
        </BrowserRouter>
    )
}

export default App
