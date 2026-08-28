import React, { useEffect, useMemo, useState } from "react";
import { apiGet, errorMessage, isAbortError } from "../../api/client";

type EventRecord = { id?: string; type?: string; source?: string; severity?: string; risk_score?: number | null; outcome?: string | null; timestamp?: string; data?: Record<string, unknown> };
type DecisionFilter = "all" | "allowed" | "challenged" | "blocked";

function textFor(event: EventRecord): string { return String(event.outcome || event.data?.decision || "observed").replace(/_/g, " "); }
function blocked(event: EventRecord): boolean { return /block|deny|reject/i.test(textFor(event)); }
function challenged(event: EventRecord): boolean { return /challenge|step.?up|mfa/i.test(textFor(event)); }
function relativeTime(value?: string): string { if (!value) return "Unknown"; const ms = new Date(value).getTime(); if (!Number.isFinite(ms)) return "Unknown"; const minutes = Math.max(0, Math.round((Date.now() - ms) / 60000)); return minutes < 1 ? "Just now" : minutes < 60 ? `${minutes}m ago` : `${Math.round(minutes / 60)}h ago`; }

export default function EventsPage() {
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [query, setQuery] = useState("");
  const [decision, setDecision] = useState<DecisionFilter>("all");
  const [severity, setSeverity] = useState("all");
  const [selected, setSelected] = useState<EventRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    apiGet<EventRecord[]>("/events?limit=200", { signal: controller.signal })
      .then((data) => { setEvents(Array.isArray(data) ? data : []); setError(null); })
      .catch((currentError) => { if (!isAbortError(currentError)) setError(errorMessage(currentError)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, []);

  const visible = useMemo(() => events.filter((event) => {
    const haystack = JSON.stringify(event).toLowerCase();
    const matchesQuery = !query.trim() || haystack.includes(query.trim().toLowerCase());
    const matchesDecision = decision === "all" || (decision === "blocked" && blocked(event)) || (decision === "challenged" && challenged(event)) || (decision === "allowed" && !blocked(event) && !challenged(event));
    const matchesSeverity = severity === "all" || String(event.severity || "unknown").toLowerCase() === severity;
    return matchesQuery && matchesDecision && matchesSeverity;
  }), [events, query, decision, severity]);

  return <div className="page events-page">
    <section className="hero-row"><div><p className="eyebrow">DETECT / INVESTIGATE</p><h1 className="page-title">Security Events</h1><p className="page-lede">Search the tenant-scoped event stream and open a decision record to understand what happened.</p></div><div className="hero-actions"><span className="environment-badge"><span className="status-dot status-dot-good" />{events.length} loaded</span></div></section>
    {error && <div className="inline-alert"><strong>Event feed unavailable</strong><span>{error}</span></div>}
    <section className="panel events-toolbar"><div className="search-field"><span>⌕</span><input aria-label="Search events" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search request ID, route, source, rule…" /></div><select aria-label="Filter decision" value={decision} onChange={(event) => setDecision(event.target.value as DecisionFilter)}><option value="all">All decisions</option><option value="allowed">Allowed</option><option value="challenged">Challenged</option><option value="blocked">Blocked</option></select><select aria-label="Filter severity" value={severity} onChange={(event) => setSeverity(event.target.value)}><option value="all">All severities</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></section>
    <section className="panel events-table-panel"><div className="panel-heading"><div><p className="eyebrow">RECORDED TELEMETRY</p><h2>{loading ? "Loading event records" : `${visible.length} event${visible.length === 1 ? "" : "s"} match`}</h2></div><span className="muted">Showing latest 200</span></div>{loading ? <div className="empty-state"><span className="loading-bar" />Loading events…</div> : visible.length ? <div className="table-scroll"><table className="data-table"><thead><tr><th>Decision</th><th>Event</th><th>Source</th><th>Severity</th><th>Risk</th><th>Time</th></tr></thead><tbody>{visible.map((event, index) => <tr key={event.id || `${event.timestamp}-${index}`} onClick={() => setSelected(event)} tabIndex={0} onKeyDown={(key) => { if (key.key === "Enter") setSelected(event); }}><td><span className={`decision-badge ${blocked(event) ? "badge-danger" : challenged(event) ? "badge-warning" : "badge-neutral"}`}>{textFor(event)}</span></td><td><b>{event.type || "Runtime event"}</b><small>{event.id || "No request ID"}</small></td><td>{event.source || "Unknown"}</td><td><span className={`severity-text severity-text-${String(event.severity || "unknown").toLowerCase()}`}>{event.severity || "Unspecified"}</span></td><td>{event.risk_score ?? "—"}</td><td>{relativeTime(event.timestamp)}</td></tr>)}</tbody></table></div> : <div className="empty-state"><strong>{events.length ? "No events match these filters" : "No runtime events recorded"}</strong><span>{events.length ? "Clear a filter or search term to see more records." : "Events will appear after an application sends traffic through the Gateway."}</span></div>}</section>
    {selected && <div className="detail-overlay" role="presentation" onClick={() => setSelected(null)}><aside className="detail-drawer" role="dialog" aria-modal="true" aria-label="Event details" onClick={(event) => event.stopPropagation()}><div className="panel-heading"><div><p className="eyebrow">EVENT DETAIL</p><h2>{selected.type || "Runtime event"}</h2></div><button className="drawer-close" type="button" onClick={() => setSelected(null)} aria-label="Close event detail">×</button></div><div className="detail-decision"><span className={`decision-icon ${blocked(selected) ? "decision-icon-danger" : challenged(selected) ? "decision-icon-warning" : "decision-icon-neutral"}`}>{blocked(selected) ? "!" : challenged(selected) ? "?" : "•"}</span><div><b>{textFor(selected)}</b><small>{relativeTime(selected.timestamp)} · {selected.source || "Unknown source"}</small></div></div><dl className="detail-grid"><dt>Request ID</dt><dd>{selected.id || "Not available"}</dd><dt>Severity</dt><dd>{selected.severity || "Not specified"}</dd><dt>Risk score</dt><dd>{selected.risk_score ?? "Not scored"}</dd><dt>Timestamp</dt><dd>{selected.timestamp || "Not available"}</dd><dt>Signals and data</dt><dd><pre>{JSON.stringify(selected.data || {}, null, 2)}</pre></dd></dl></aside></div>}
  </div>;
}
