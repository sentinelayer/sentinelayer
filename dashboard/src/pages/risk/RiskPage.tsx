import React, { useEffect, useMemo, useState } from "react";
import { api, type ApiError } from "../../api/client";

type RiskDecision = {
  id: string;
  event_id: string;
  score: number;
  confidence: number;
  action: string;
  factors: Record<string, unknown>;
  model_version: string;
  created_at: string;
};

function errorMessage(error: unknown): string {
  if (error && typeof error === "object" && "message" in error) {
    return String((error as ApiError).message);
  }
  return "Risk decisions could not be loaded.";
}

export const RiskPage: React.FC = () => {
  const [decisions, setDecisions] = useState<RiskDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api.get<RiskDecision[]>("/events/decisions?limit=100")
      .then((data) => {
        if (active) setDecisions(data);
      })
      .catch((err: unknown) => {
        if (active) setError(errorMessage(err));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const summary = useMemo(() => {
    if (!decisions.length) return { average: 0, highest: 0, blocked: 0 };
    return {
      average: Math.round(decisions.reduce((total, item) => total + item.score, 0) / decisions.length),
      highest: Math.max(...decisions.map((item) => item.score)),
      blocked: decisions.filter((item) => item.action === "BLOCK").length,
    };
  }, [decisions]);

  return (
    <div className="page risk-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">RISK INTELLIGENCE</p>
          <h1>Risk decisions</h1>
          <p className="muted">Durable decisions recorded by the control plane for the current tenant.</p>
        </div>
      </div>

      {loading && <p className="muted">Loading risk decisions…</p>}
      {error && <p className="error" role="alert">{error}</p>}

      {!loading && !error && (
        decisions.length ? (
          <>
            <div className="metric-grid" aria-label="Risk summary">
              <div className="metric-card"><span>Decisions</span><strong>{decisions.length}</strong></div>
              <div className="metric-card"><span>Average score</span><strong>{summary.average}</strong></div>
              <div className="metric-card"><span>Highest score</span><strong>{summary.highest}</strong></div>
              <div className="metric-card"><span>Blocked</span><strong>{summary.blocked}</strong></div>
            </div>
            <div className="table-card">
              <div className="table-scroll">
                <table>
                  <thead><tr><th>Action</th><th>Score</th><th>Confidence</th><th>Model</th><th>Created</th></tr></thead>
                  <tbody>
                    {decisions.map((decision) => (
                      <tr key={decision.id}>
                        <td><span className={`status-pill status-${decision.action.toLowerCase()}`}>{decision.action}</span></td>
                        <td>{decision.score}</td>
                        <td>{decision.confidence}%</td>
                        <td>{decision.model_version}</td>
                        <td>{new Date(decision.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : <div className="empty-state"><h2>No risk decisions yet</h2><p className="muted">Decisions will appear here after authenticated runtime events are recorded.</p></div>
      )}
    </div>
  );
};

export default RiskPage;
