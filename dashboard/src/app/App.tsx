import React, { useState } from "react";
import { isLoggedIn, logout } from "../api/client";
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

type Tab =
  | "overview"
  | "applications"
  | "policies"
  | "incidents"
  | "events"
  | "alerts"
  | "evidence"
  | "risk"
  | "configuration";

const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "applications", label: "Applications" },
  { id: "policies", label: "Policies" },
  { id: "incidents", label: "Incidents" },
  { id: "events", label: "Events" },
  { id: "alerts", label: "Alerts" },
  { id: "evidence", label: "Evidence" },
  { id: "risk", label: "Risk" },
  { id: "configuration", label: "Config" },
];

export default function App() {
  const [authed, setAuthed] = useState(isLoggedIn());
  const [tab, setTab] = useState<Tab>("overview");

  if (!authed) {
    return <LoginPage onSuccess={() => setAuthed(true)} />;
  }

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", minHeight: "100vh", background: "#0a0a0a", color: "#e8e8e8" }}>
      <nav
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 8,
          padding: 12,
          borderBottom: "1px solid #333",
          alignItems: "center",
        }}
      >
        <strong style={{ color: "#00ff88", marginRight: 12 }}>SentinelLayer</strong>
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              background: tab === t.id ? "#00ff88" : "#1a1a1a",
              color: tab === t.id ? "#0a0a0a" : "#ccc",
              border: "1px solid #333",
              padding: "6px 10px",
              cursor: "pointer",
              borderRadius: 4,
            }}
          >
            {t.label}
          </button>
        ))}
        <button
          onClick={() => {
            logout();
            setAuthed(false);
          }}
          style={{ marginLeft: "auto", background: "#331111", color: "#ff8888", border: "1px solid #553333", padding: "6px 10px", cursor: "pointer", borderRadius: 4 }}
        >
          Logout
        </button>
      </nav>
      <main style={{ padding: 16 }}>
        {tab === "overview" && <OverviewPage />}
        {tab === "applications" && <ApplicationsPage />}
        {tab === "policies" && <PoliciesPage />}
        {tab === "incidents" && <IncidentsPage />}
        {tab === "events" && <EventsPage />}
        {tab === "alerts" && <AlertsPage />}
        {tab === "evidence" && <EvidenceList />}
        {tab === "risk" && <RiskPage />}
        {tab === "configuration" && <ConfigurationPage />}
      </main>
    </div>
  );
}
