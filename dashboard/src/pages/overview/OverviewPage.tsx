import React, { useEffect, useState } from "react";
import { apiGet, ApiError } from "../../api/client";

type Counts = { applications: number; policies: number; incidents: number };

export default function OverviewPage() {
  const [counts, setCounts] = useState<Counts | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [apps, policies, incidents] = await Promise.all([
          apiGet<unknown[]>("/api/v1/applications").catch(() => []),
          apiGet<unknown[]>("/api/v1/policies").catch(() => []),
          apiGet<unknown[]>("/api/v1/incidents").catch(() => []),
        ]);
        if (!cancelled) {
          setCounts({
            applications: Array.isArray(apps) ? apps.length : 0,
            policies: Array.isArray(policies) ? policies.length : 0,
            incidents: Array.isArray(incidents) ? incidents.length : 0,
          });
        }
      } catch (e) {
        const err = e as ApiError;
        if (!cancelled) setError(err?.message || "Failed to load overview");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <div className="page">Loading overview…</div>;
  if (error) return <div className="page error">API error: {error}</div>;

  return (
    <div className="page">
      <h1>Overview</h1>
      <p>Live counts from control plane (tenant-scoped).</p>
      <ul>
        <li>Applications: {counts?.applications ?? 0}</li>
        <li>Policies: {counts?.policies ?? 0}</li>
        <li>Incidents: {counts?.incidents ?? 0}</li>
      </ul>
    </div>
  );
}
