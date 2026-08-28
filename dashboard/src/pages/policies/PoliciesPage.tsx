import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiPost, errorMessage, isAbortError } from "../../api/client";
import { canMutate, roleLabel } from "../../app/permissions";

type Policy = { id: string; name: string; tenant_id?: string; application_id?: string | null; version?: number; rules?: Record<string, unknown>; signature_valid?: boolean; created_at?: string };
function formatDate(value?: string): string { if (!value) return "Date unavailable"; const date = new Date(value); return Number.isNaN(date.getTime()) ? "Date unavailable" : date.toLocaleDateString(); }

export default function PoliciesPage() {
  const [items, setItems] = useState<Policy[]>([]);
  const [name, setName] = useState("");
  const [applicationId, setApplicationId] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const canEdit = canMutate();
  async function load(signal?: AbortSignal) {
    try {
      const data = await apiGet<Policy[]>("/policies", { signal });
      setItems(Array.isArray(data) ? data : []);
      setError(null);
    } catch (currentError) {
      if (!isAbortError(currentError)) setError(errorMessage(currentError));
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }
  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, []);
  async function create(event: React.FormEvent) { event.preventDefault(); setCreating(true); setError(null); try { await apiPost("/policies", { name: name.trim(), application_id: applicationId.trim() || null, rules: { mode: "monitor" } }); setName(""); setApplicationId(""); await load(); } catch (currentError) { setError(errorMessage(currentError)); } finally { setCreating(false); } }
  const verified = items.filter((item) => item.signature_valid).length;
  return <div className="page"><section className="hero-row"><div><p className="eyebrow">GOVERN / POLICY CONTROL</p><h1 className="page-title">Policies</h1><p className="page-lede">Manage signed policy records through a change workflow. New policies start in monitor mode; publish and rollback controls live in the policy detail flow.</p></div><Link className="secondary-button compact-button" to="/configuration">Configuration</Link></section>{error && <div className="inline-alert"><strong>Policy action failed</strong><span>{error}</span><button className="text-button" type="button" onClick={() => void load()}>Retry</button></div>}<section className="metric-grid metric-grid-four"><article className="metric-card metric-card-accent"><span>Policy records</span><strong>{items.length}</strong><small>Tenant-scoped policies</small></article><article className="metric-card metric-card-success"><span>Verified versions</span><strong>{verified}</strong><small>Signature verified in response</small></article><article className="metric-card"><span>Unverified</span><strong>{items.length - verified}</strong><small>Review before relying on version</small></article><article className="metric-card"><span>Change workflow</span><strong>5</strong><small>Draft · validate · review · publish · rollback</small></article></section><section className="dashboard-grid"><article className="panel"><div className="panel-heading"><div><p className="eyebrow">POLICY INTAKE</p><h2>Create a policy record</h2></div><span className="environment-badge">Versioned</span></div>{canEdit ? <form className="application-form" onSubmit={create}><label>Policy name<input value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Public API baseline" required maxLength={255} /></label><label>Application ID <span className="muted">(optional)</span><input value={applicationId} onChange={(event) => setApplicationId(event.target.value)} placeholder="Scope to an application record" /></label><button className="primary-button" type="submit" disabled={creating}>{creating ? "Creating…" : "Create policy"}</button></form> : <div className="permission-note" role="note"><strong>Viewer access</strong><span>Your {roleLabel()} role can review policies but cannot create or publish changes.</span></div>}</article><article className="panel"><div className="panel-heading"><div><p className="eyebrow">CHANGE CONTROL</p><h2>Safe by default</h2></div></div><div className="setup-steps"><div className="setup-step setup-step-active"><b>01</b><span><strong>Draft and validate</strong><small>Keep changes reviewable before activation.</small></span></div><div className="setup-step"><b>02</b><span><strong>Review and publish</strong><small>Keep version, signature, and actor metadata.</small></span></div><div className="setup-step"><b>03</b><span><strong>Monitor and rollback</strong><small>Use the diff view to compare versions.</small></span></div></div></article></section><section className="panel application-list-panel"><div className="panel-heading"><div><p className="eyebrow">POLICY REGISTER</p><h2>{loading ? "Loading policies" : `${items.length} policy${items.length === 1 ? "" : "ies"}`}</h2></div><span className="muted">Signed metadata included where available</span></div>{loading ? <div className="empty-state"><span className="loading-bar" />Loading policies…</div> : items.length ? <div className="policy-grid">{items.map((item) => <article className="policy-card" key={item.id}><div className="application-card-top"><span className={`decision-badge ${item.signature_valid ? "badge-neutral" : "badge-warning"}`}>{item.signature_valid ? "Verified" : "Review"}</span><span className="muted">v{item.version || 1}</span></div><h3>{item.name}</h3><p>{item.application_id ? `Application ${item.application_id}` : "Workspace-wide policy"}</p><code>{item.id}</code><div className="policy-card-footer"><span>Created {formatDate(item.created_at)}</span><Link className="inline-link" to={`/policies/${item.id}/edit`}>Open →</Link></div></article>)}</div> : <div className="empty-state"><strong>No policy records</strong><span>Create a baseline policy above; it will be stored with a version record.</span></div>}</section></div>;
}
