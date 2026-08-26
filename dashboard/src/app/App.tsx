import React, { useState } from "react";
import { isLoggedIn, logout } from "../api/client";
import LoginPage from "../pages/login/LoginPage";
import OverviewPage from "../pages/overview/OverviewPage";
import ApplicationsPage from "../pages/applications/ApplicationsPage";
import PoliciesPage from "../pages/policies/PoliciesPage";
import IncidentsPage from "../pages/incidents/IncidentsPage";

type Tab = "overview" | "applications" | "policies" | "incidents";

export default function App() {
  const [authed, setAuthed] = useState(isLoggedIn());
  const [tab, setTab] = useState<Tab>("overview");

  if (!authed) {
    return <LoginPage onSuccess={() => setAuthed(true)} />;
  }

  return (
    <div>
      <nav style={{ display: "flex", gap: 12, padding: 12, borderBottom: "1px solid #333" }}>
        <button onClick={() => setTab("overview")}>Overview</button>
        <button onClick={() => setTab("applications")}>Applications</button>
        <button onClick={() => setTab("policies")}>Policies</button>
        <button onClick={() => setTab("incidents")}>Incidents</button>
        <button
          onClick={() => {
            logout();
            setAuthed(false);
          }}
        >
          Logout
        </button>
      </nav>
      {tab === "overview" && <OverviewPage />}
      {tab === "applications" && <ApplicationsPage />}
      {tab === "policies" && <PoliciesPage />}
      {tab === "incidents" && <IncidentsPage />}
    </div>
  );
}
