import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, ApiError } from "../../api/client";

type Application = { id?: string; name?: string; status?: string; domain?: string; upstream_url?: string };
type Policy = { id?: string; name?: string; status?: string; version?: number };
type Incident = { id?: string; title?: string; severity?: string; status?: string; created_at?: string; updated_at?: string };
type Event = { id?: string; type?: string; source?: string; severity?: string; risk_score?: number | null; outcome?: string | null; timestamp?: string; data?: Record<string, unknown> };
type Counts = { applications: Application[]; policies: Policy[]; incidents: Incident[]; events: Event[] };

function errorMessage(error: unknown): string {
  return (error as ApiError)?.message || (error instanceof Error ? error.message : "Unable to load workspace data");
}

function relativeTime(value?: string): string {
  if (!value) return "Unknown time";
  const timestamp = new Date(value).getTime();
  if (!Number.isFinite(timestamp)) return "Unknown time";
  const minutes = Math.max(0, Math.round((Date.now() - timestamp) / 60000));
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

function decisionLabel(event: Event): string {
  return String(event.outcome || event.data?.decision || "Observed").replace(/_/g, " ");
}

export default function OverviewPage() {
  const [data, setData] = useState<Counts | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const [applications, policies, incidents, events] = await Promise.all([
          apiGet<Application[]>("/applications"),
          apiGet<Policy[]>("/policies"),
          apiGet<Incident[]>("/incidents"),
          apiGet<Event[]>("/events?limit=8"),
        ]);
        if (!cancelled) setData({ applications: applications || [], policies: policies || [], incidents: incidents || [], events: events || [] });
      } catch (currentError) {
        if (!cancelled) setError(errorMessage(currentError));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const openIncidents = useMemo(() => (data?.incidents || []).filter((incident) => !["resolved", "closed"].includes(String(incident.status || "").toLowerCase())), [data]);
  const blockedEvents = useMemo(() => (data?.events || []).filter((event) => /block|deny|reject/i.test(decisionLabel(event))), [data]);

  if (loading) return <div className="page-state"><span className="loading-bar" />Loading your security workspace…</div>;
  if (error) return <div className="page-state page-state-error"><strong>Workspace data unavailable</strong><span>{error}</span><button className="secondary-button" type="button" onClick={() => window.location.reload()}>Try again</button></div>;

  const applications = data?.applications || [];
  const policies = data?.policies || [];
  const events = data?.events || [];
  const hasWorkspace = applications.length > 0;

  return (
    <div className="page overview-page">
      <section className="hero-row">
        <div>
          <p className="eyebrow">SECURITY OPERATIONS</p>
          <h1 className="page-title">Good evening. Here is your protection posture.</h1>
          <p className="page-lede">A tenant-scoped view of the traffic, decisions, and actions recorded by SentinelLayer.</p>
        </div>
        <Link className="primary-button compact-button" to={hasWorkspace ? "/live-protection" : "/applications"}>{hasWorkspace ? "Open live protection" : "Connect an application"}</Link>
      </section>

      {!hasWorkspace && (
        <section className="setup-banner">
          <div className="setup-icon">01</div>
          <div className="setup-copy"><p className="eyebrow">FIRST-RUN SETUP</p><h2>Your workspace is ready. Connect the first application.</h2><p>No traffic is shown until an application sends requests through the Gateway. SentinelLayer will not label an application protected before verification.</p></div>
          <Link className="secondary-button" to="/applications">Start setup</Link>
        </section>
      )}

      <section className="metric-grid metric-grid-five" aria-label="Workspace summary">
        <article className="metric-card metric-card-accent"><span>Applications</span><strong>{applications.length}</strong><small>{hasWorkspace ? "Connected to workspace" : "Nothing connected yet"}</small></article>
        <article className="metric-card"><span>Policies</span><strong>{policies.length}</strong><small>{policies.length ? "Configured policy records" : "Create a baseline policy"}</small></article>
        <article className="metric-card"><span>Open incidents</span><strong>{openIncidents.length}</strong><small>{openIncidents.length ? "Needs investigation" : "No open incidents recorded"}</small></article>
        <article className="metric-card"><span>Recent events</span><strong>{events.length}</strong><small>{events.length ? "Latest recorded activity" : "Waiting for runtime traffic"}</small></article>
        <article className="metric-card"><span>Recent blocks</span><strong>{blockedEvents.length}</strong><small>{blockedEvents.length ? "From loaded event window" : "No blocks in loaded window"}</small></article>
      </section>

      <section className="dashboard-grid">
        <article className="panel panel-large">
          <div className="panel-heading"><div><p className="eyebrow">RECENT ACTIVITY</p><h2>Security decision stream</h2></div><Link className="inline-link" to="/events">View all events</Link></div>
          {events.length ? <div className="event-stream">{events.map((event) => <Link className="event-row" to="/events" key={event.id || `${event.timestamp}-${event.type}`}><span className={`decision-dot ${/block|deny|reject/i.test(decisionLabel(event)) ? "decision-dot-danger" : "decision-dot-neutral"}`} /><span className="event-main"><b>{event.type || "Runtime event"}</b><small>{event.source || "Unknown source"} · {relativeTime(event.timestamp)}</small></span><span className="event-decision">{decisionLabel(event)}</span>{event.risk_score !== null && event.risk_score !== undefined && <span className="event-score">Risk {event.risk_score}</span>}</Link>)}</div> : <div className="empty-state"><strong>No runtime events yet</strong><span>Connect an application and route traffic through the Gateway to see decisions here.</span><Link className="inline-link" to="/applications">Connect an application</Link></div>}
        </article>
        <article className="panel">
          <div className="panel-heading"><div><p className="eyebrow">RESPONSE QUEUE</p><h2>Active incidents</h2></div><Link className="inline-link" to="/incidents">Open incidents</Link></div>
          {openIncidents.length ? <div className="incident-list">{openIncidents.slice(0, 5).map((incident) => <Link className="incident-row" to="/incidents" key={incident.id}><span className={`severity-dot severity-${String(incident.severity || "medium").toLowerCase()}`} /><span><b>{incident.title || "Untitled incident"}</b><small>{incident.status || "Open"} · {relativeTime(incident.updated_at || incident.created_at)}</small></span><span className="chevron">›</span></Link>)}</div> : <div className="empty-state"><strong>Nothing requires attention</strong><span>Open incidents will appear here when recorded by the control plane.</span></div>}
        </article>
      </section>

      <section className="dashboard-grid dashboard-grid-three">
        <article className="panel"><div className="panel-heading"><div><p className="eyebrow">PROTECTION SURFACE</p><h2>Applications</h2></div><Link className="inline-link" to="/applications">Manage</Link></div>{applications.length ? applications.slice(0, 4).map((application) => <div className="compact-row" key={application.id}><span className="status-dot status-dot-good" /><span><b>{application.name || application.domain || "Unnamed application"}</b><small>{application.domain || application.upstream_url || "Configuration details unavailable"}</small></span><span className="status-label">{application.status || "Connected"}</span></div>) : <div className="empty-state"><span>No applications connected.</span></div>}</article>
        <article className="panel"><div className="panel-heading"><div><p className="eyebrow">GOVERNANCE</p><h2>Policy posture</h2></div><Link className="inline-link" to="/policies">Review</Link></div><div className="posture-score"><strong>{policies.length ? policies.length : "—"}</strong><span>{policies.length ? "policy records available" : "No policy records yet"}</span></div><p className="panel-note">Policy changes should move through draft, validation, review, publish, and rollback workflows.</p></article>
        <article className="panel"><div className="panel-heading"><div><p className="eyebrow">RUNTIME</p><h2>Service health</h2></div><Link className="inline-link" to="/configuration">Details</Link></div><div className="health-row"><span className="status-dot status-dot-good" /><div><b>Control plane reachable</b><small>Health endpoint responded for this session</small></div></div><div className="health-row"><span className="status-dot status-dot-muted" /><div><b>Traffic baseline</b><small>{events.length ? "Activity detected in current window" : "Waiting for an application to send traffic"}</small></div></div></article>
      </section>
    </div>
  );
}
