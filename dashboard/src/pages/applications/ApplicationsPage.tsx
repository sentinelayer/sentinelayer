import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiPost, ApiError } from "../../api/client";

type App = { id: string; name: string; tenant_id?: string; environment?: string; status?: string };
function errorMessage(error: unknown): string { return (error as ApiError)?.message || (error instanceof Error ? error.message : "Unable to load applications"); }

export default function ApplicationsPage() {
  const [apps, setApps] = useState<App[]>([]);
  const [name, setName] = useState("");
  const [environment, setEnvironment] = useState("production");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try { const data = await apiGet<App[]>("/applications"); setApps(Array.isArray(data) ? data : []); setError(null); } catch (currentError) { setError(errorMessage(currentError)); } finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);
  async function create(event: React.FormEvent) {
    event.preventDefault(); setCreating(true); setError(null);
    try { await apiPost("/applications", { name: name.trim(), environment }); setName(""); await load(); } catch (currentError) { setError(errorMessage(currentError)); } finally { setCreating(false); }
  }

  return <div className="page">
    <section className="hero-row"><div><p className="eyebrow">PROTECT / APPLICATIONS</p><h1 className="page-title">Applications</h1><p className="page-lede">Register the applications that belong to this workspace. Protection status only becomes meaningful after traffic is routed through the Gateway.</p></div><Link className="secondary-button compact-button" to="/live-protection">View live protection</Link></section>
    {error && <div className="inline-alert"><strong>Application action failed</strong><span>{error}</span><button className="text-button" type="button" onClick={() => void load()}>Retry</button></div>}
    <section className="dashboard-grid">
      <article className="panel"><div className="panel-heading"><div><p className="eyebrow">CONNECT A SURFACE</p><h2>Register an application</h2></div><span className="environment-badge">Step 1 of 3</span></div><p className="panel-note setup-note">Create the workspace record first. Gateway routing and verification should be completed before an application is described as protected.</p><form className="application-form" onSubmit={create}><label>Application name<input value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Customer API" required maxLength={120} /></label><label>Environment<select value={environment} onChange={(event) => setEnvironment(event.target.value)}><option value="production">Production</option><option value="staging">Staging</option><option value="development">Development</option></select></label><button className="primary-button" type="submit" disabled={creating}>{creating ? "Creating…" : "Create application"}</button></form></article>
      <article className="panel"><div className="panel-heading"><div><p className="eyebrow">SETUP PATH</p><h2>From record to protection</h2></div></div><div className="setup-steps"><div className="setup-step setup-step-active"><b>01</b><span><strong>Register application</strong><small>Create a tenant-scoped application record.</small></span></div><div className="setup-step"><b>02</b><span><strong>Route traffic</strong><small>Configure the Gateway and upstream in your deployment.</small></span></div><div className="setup-step"><b>03</b><span><strong>Verify decisions</strong><small>Confirm allowed and blocked requests in Live Protection.</small></span></div></div></article>
    </section>
    <section className="panel application-list-panel"><div className="panel-heading"><div><p className="eyebrow">PROTECTION SURFACE</p><h2>{loading ? "Loading applications" : `${apps.length} application${apps.length === 1 ? "" : "s"}`}</h2></div><span className="muted">Tenant-scoped records</span></div>{loading ? <div className="empty-state"><span className="loading-bar" />Loading applications…</div> : apps.length ? <div className="application-grid">{apps.map((application) => <article className="application-card" key={application.id}><div className="application-card-top"><span className="status-dot status-dot-good" /><span className="status-label">{application.environment || "Production"}</span></div><h3>{application.name}</h3><code>{application.id}</code><p>Routing verification is handled by the Gateway runtime.</p><Link className="inline-link" to="/live-protection">Open live protection →</Link></article>)}</div> : <div className="empty-state"><strong>No applications registered</strong><span>Create the first application above to begin the protection setup.</span></div>}</section>
  </div>;
}
