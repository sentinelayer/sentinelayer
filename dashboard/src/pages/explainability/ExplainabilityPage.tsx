import React, { useEffect, useState } from "react";
import { api, errorMessage, isAbortError } from "../../api/client";

type RawDecision = { action?: string; reason?: string; timestamp?: string; factors?: Record<string, unknown>; policy?: string; version?: string | number; risk_score?: number | null };
type Decision = RawDecision & { what: string; why: string; who: string; when: string; signal: Record<string, unknown>; policy: string; version: string | number };

export const ExplainabilityPage: React.FC = () => {
  const [decision, setDecision] = useState<Decision | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    api.get<RawDecision>("/explainability/latest", { signal: controller.signal })
      .then((data) => setDecision({ ...data, what: `Decision was ${data.action || "observed"}`, why: data.reason || "No explanation", who: "system", when: data.timestamp || new Date().toISOString(), signal: data.factors || {}, policy: data.policy || "default", version: data.version || "1.0" }))
      .then(() => setError(null))
      .catch((currentError) => { if (!isAbortError(currentError)) setError(errorMessage(currentError)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, []);
  if (loading) return <div className="page-state"><span className="loading-bar" />Loading decision explanation…</div>;
  if (error) return <div className="page-state page-state-error"><strong>Decision explanation unavailable</strong><span>{error}</span></div>;
  return <div className="page explainability-page"><h1 className="page-title">Decision Explainability</h1>{decision ? <div className="decision-detail"><h2>WHAT</h2><p>{decision.what}</p><h2>WHY</h2><p>{decision.why}</p><h2>WHO</h2><p>{decision.who}</p><h2>WHEN</h2><p>{decision.when}</p><h2>SIGNAL</h2><ul>{Object.entries(decision.signal).map(([key, value]) => <li key={key}>{key}: {String(value)}</li>)}</ul><h2>SCORE</h2><p>{decision.risk_score ?? "Not scored"}</p><h2>POLICY</h2><p>{decision.policy}</p><h2>VERSION</h2><p>{decision.version}</p></div> : <p>No decision data available</p>}</div>;
};

export default ExplainabilityPage;
