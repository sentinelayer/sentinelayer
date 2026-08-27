import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { isLoggedIn } from "../api/client";
import { Layout } from "../components/Layout";
import LoginPage from "../pages/login/LoginPage";
import OverviewPage from "../pages/overview/OverviewPage";
import ApplicationsPage from "../pages/applications/ApplicationsPage";
import PoliciesPage from "../pages/policies/PoliciesPage";
import IncidentsPage from "../pages/incidents/IncidentsPage";
import EventsPage from "../pages/events/EventsPage";
import AlertsPage from "../pages/alerts/AlertsPage";
import EvidenceList from "../pages/evidence/EvidenceList";
import RiskPage from "../pages/risk/RiskPage";
import ConfigurationPage from "../pages/configuration/ConfigurationPage";
import AttackGraphPage from "../pages/attack-graph/AttackGraphPage";
import HeatmapPage from "../pages/heatmap/HeatmapPage";
import UserRiskPage from "../pages/user-risk/UserRiskPage";
import ExplainabilityPage from "../pages/explainability/ExplainabilityPage";
import SLAPage from "../pages/sla/SLAPage";
import BreakGlassPage from "../pages/admin/break-glass/BreakGlassPage";
import HighRiskActionsPage from "../pages/admin/high-risk/HighRiskActionsPage";

function RequireAuth({ children }: { children: React.ReactNode }) {
  if (!isLoggedIn()) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage onSuccess={() => (window.location.href = "/")} />} />
        <Route path="/" element={<RequireAuth><OverviewPage /></RequireAuth>} />
        <Route path="/applications" element={<RequireAuth><ApplicationsPage /></RequireAuth>} />
        <Route path="/events" element={<RequireAuth><EventsPage /></RequireAuth>} />
        <Route path="/alerts" element={<RequireAuth><AlertsPage /></RequireAuth>} />
        <Route path="/incidents" element={<RequireAuth><IncidentsPage /></RequireAuth>} />
        <Route path="/evidence" element={<RequireAuth><EvidenceList /></RequireAuth>} />
        <Route path="/risk" element={<RequireAuth><RiskPage /></RequireAuth>} />
        <Route path="/attack-graph" element={<RequireAuth><AttackGraphPage /></RequireAuth>} />
        <Route path="/heatmap" element={<RequireAuth><HeatmapPage /></RequireAuth>} />
        <Route path="/user-risk" element={<RequireAuth><UserRiskPage /></RequireAuth>} />
        <Route path="/policies" element={<RequireAuth><PoliciesPage /></RequireAuth>} />
        <Route path="/configuration" element={<RequireAuth><ConfigurationPage /></RequireAuth>} />
        <Route path="/explainability" element={<RequireAuth><ExplainabilityPage /></RequireAuth>} />
        <Route path="/sla" element={<RequireAuth><SLAPage /></RequireAuth>} />
        <Route path="/admin/break-glass" element={<RequireAuth><BreakGlassPage /></RequireAuth>} />
        <Route path="/admin/high-risk-actions" element={<RequireAuth><HighRiskActionsPage /></RequireAuth>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
