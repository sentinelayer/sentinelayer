import React, { useEffect, useState } from "react";
import { api, errorMessage, isAbortError } from "../../api/client";

type HeatmapCell = { endpoint?: string; risk?: number };

export const HeatmapPage: React.FC = () => {
  const [data, setData] = useState<HeatmapCell[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    api.get<HeatmapCell[]>("/heatmap", { signal: controller.signal })
      .then((value) => { setData(Array.isArray(value) ? value : []); setError(null); })
      .catch((currentError) => { if (!isAbortError(currentError)) setError(errorMessage(currentError)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, []);
  if (loading) return <div className="page-state"><span className="loading-bar" />Loading risk heatmap…</div>;
  if (error) return <div className="page-state page-state-error"><strong>Risk heatmap unavailable</strong><span>{error}</span></div>;
  return <div className="page heatmap-page"><h1 className="page-title">Risk Heatmap</h1>{data.length === 0 ? <p>No risk data available</p> : <div className="heatmap-grid">{data.map((cell, index) => { const risk = Number.isFinite(cell.risk) ? cell.risk : 0; return <div key={`${cell.endpoint || "unknown"}-${index}`} className={`heatmap-cell risk-${risk}`}>{cell.endpoint || "Unknown"}<span className="heatmap-value">{risk}</span></div>; })}</div>}</div>;
};

export default HeatmapPage;
