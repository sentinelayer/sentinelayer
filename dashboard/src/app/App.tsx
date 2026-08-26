import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Login } from '../pages/auth/Login'
import { OverviewPage } from '../pages/overview/OverviewPage'
import { PolicyList } from '../pages/policies/PolicyList'
import { IncidentList } from '../pages/incidents/IncidentList'
import { EvidenceList } from '../pages/evidence/EvidenceList'
import { RiskPage } from '../pages/risk/RiskPage'
import { SLAPage } from '../pages/sla/SLAPage'
import { Guards } from './guards'

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/" element={<Guards><OverviewPage /></Guards>} />
                <Route path="/policies" element={<Guards><PolicyList /></Guards>} />
                <Route path="/incidents" element={<Guards><IncidentList /></Guards>} />
                <Route path="/evidence" element={<Guards><EvidenceList /></Guards>} />
                <Route path="/risk" element={<Guards><RiskPage /></Guards>} />
                <Route path="/sla" element={<Guards><SLAPage /></Guards>} />
            </Routes>
        </BrowserRouter>
    )
}

export default App
