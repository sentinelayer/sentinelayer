import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, errorMessage, isAbortError } from "../../api/client";

type EventRecord = { id?: string; type?: string; source?: string; severity?: string; risk_score?: number | null; outcome?: string | null; timestamp?: string; data?: Record<string, unknown> };
type Filter = "all" | "allowed" | "blocked" | "challenged";

function label(event: EventRecord): string {
  return String(event.outcome || event.data?.decision || "observed").replace(/_/g, " ").toLowerCase();
}
function isBlocked(event: EventRecord): boolean { return /block|deny|reject/i.test(label(event)); }
function isChallenged(event: EventRecord): boolean { return /challenge|step.?up|mfa/i.test(label(event)); }
function isAllowed(event: EventRecord): boolean { return /allow|permit|forward|success/i.test(label(event)); }
function relativeTime(value?: string): string {
  if (!value) return "Unknown time";
  const minutes = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 60000));
  return minutes < 1 ? "Just now" : minutes < 60 ? `${minutes}m ago` : `${Math.round(minutes / 60)}h ago`;
}

export default function LiveProtectionPage() {
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const load = useCallback(async (background = false, signal?: AbortSignal) => {
    if (background) setRefreshing(true); else setLoading(true);
    try {
      const next = await apiGet<EventRecord[]>("/events?limit=50", { signal });
      setEvents(Array.isArray(next) ? next : []);
      setError(null);
      setLastUpdated(new Date());
    } catch (currentError) {
      if (!isAbortError(currentError)) setError(errorMessage(currentError));
    } finally {
      if (!signal?.aborted) { setLoading(false); setRefreshing(false); }
    }
  }, []);

  useEffect(() => {
    let activeController: AbortController | null = new AbortController();
    void load(false, activeController.signal);
    const timer = window.setInterval(() => {
      activeController?.abort();
      activeController = new AbortController();
      void load(true, activeController.signal);
    }, 10000);
    return () => { window.clearInterval(timer); activeController?.abort(); };
  }, [load]);

  const visibleEvents = useMemo(() => events.filter((event) => filter === "all" || (filter === "blocked" && isBlocked(event)) || (filter === "challenged" && isChallenged(event)) || (filter === "allowed" && isAllowed(event))), [events, filter]);
  const blocked = events.filter(isBlocked).length;
  const challenged = events.filter(isChallenged).length;
  const allowed = events.filter(isAllowed).length;

  return (
    <div className="page live-page">
      <section className="hero-row">
        <div><p className="eyebrow">PROTECT / LIVE VIEW</p><h1 className="page-title">Live Protection</h1><p className="page-lede">Watch security decisions recorded by the Gateway for this workspace. This view refreshes every ten seconds.</p></div>
        <div className="hero-actions"><span className="live-indicator"><span className="pulse-dot" />{refreshing ? "Refreshing" : "Polling live"}</span><button className="secondary-button compact-button" type="button" onClick={() => void load(true)}>Refresh now</button></div>
      </section>

      {error && <div className="inline-alert"><strong>Live feed unavailable</strong><span>{error}</span><button className="text-button" type="button" onClick={() => void load()}>Retry</button></div>}
      <section className="metric-grid metric-grid-four">
        <article className="metric-card"><span>Events loaded</span><strong>{events.length}</strong><small>{lastUpdated ? `Updated ${relativeTime(lastUpdated.toISOString())}` : "Waiting for data"}</small></article>
        <article className="metric-card metric-card-success"><span>Allowed</span><strong>{allowed}</strong><small>Matched loaded decisions</small></article>
        <article className="metric-card metric-card-warning"><span>Challenged</span><strong>{challenged}</strong><small>Step-up or challenge outcomes</small></article>
        <article className="metric-card metric-card-danger"><span>Blocked</span><strong>{blocked}</strong><small>Denied in loaded window</small></article>
      </section>

      <section className="pipeline-card" aria-label="SentinelLayer decision pipeline">
        <div className="pipeline-step pipeline-step-active"><b>01</b><span>Incoming request</span></div><span className="pipeline-arrow">→</span><div className="pipeline-step"><b>02</b><span>WAF & rate limit</span></div><span className="pipeline-arrow">→</span><div className="pipeline-step"><b>03</b><span>Behavior & risk</span></div><span className="pipeline-arrow">→</span><div className="pipeline-step"><b>04</b><span>Decision & upstream</span></div>
      </section>

      <section className="panel event-feed-panel">
        <div className="panel-heading"><div><p className="eyebrow">REQUEST TELEMETRY</p><h2>Decision stream</h2></div><div className="filter-tabs" role="tablist" aria-label="Filter decisions">{(["all", "allowed", "challenged", "blocked"] as Filter[]).map((item) => <button type="button" key={item} className={filter === item ? "filter-tab filter-tab-active" : "filter-tab"} onClick={() => setFilter(item)}>{item[0].toUpperCase() + item.slice(1)}</button>)}</div></div>
        {loading ? <div className="empty-state"><span className="loading-bar" />Loading recorded events…</div> : visibleEvents.length ? <div className="live-event-list">{visibleEvents.map((event) => <Link className="live-event" to="/events" key={event.id || `${event.timestamp}-${event.type}`}><span className={`decision-icon ${isBlocked(event) ? "decision-icon-danger" : isChallenged(event) ? "decision-icon-warning" : "decision-icon-neutral"}`}>{isBlocked(event) ? "!" : isChallenged(event) ? "?" : "•"}</span><span className="live-event-content"><b>{event.type || "Runtime event"}</b><small>{event.source || "Unknown source"} · {relativeTime(event.timestamp)} · {event.id || "No request ID"}</small></span><span className={`decision-badge ${isBlocked(event) ? "badge-danger" : isChallenged(event) ? "badge-warning" : "badge-neutral"}`}>{label(event)}</span>{event.risk_score !== null && event.risk_score !== undefined && <span className="risk-value">{event.risk_score}<small>risk</small></span>}<span className="chevron">›</span></Link>)}</div> : <div className="empty-state"><strong>{events.length ? "No events match this filter" : "No runtime events recorded"}</strong><span>{events.length ? "Choose another decision filter to continue." : "Traffic will appear here after an application sends requests through the Gateway."}</span>{!events.length && <Link className="inline-link" to="/applications">Connect an application</Link>}</div>}
      </section>
    </div>
  );
}
