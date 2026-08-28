import React, { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost, errorMessage, isAbortError } from "../../../api/client";

type Session = { id: string; user_id: string; requested_by?: string; reason: string; status: string; created_at?: string; expires_at?: string; approved_by?: string | null; approved_at?: string | null; revoked_at?: string | null };
function date(value?: string | null): string { if (!value) return "Not recorded"; const current = new Date(value); return Number.isNaN(current.getTime()) ? "Not recorded" : current.toLocaleString(); }
function isExpired(value?: string): boolean { return !!value && new Date(value).getTime() <= Date.now(); }

export default function BreakGlassPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  async function load(signal?: AbortSignal) {
    try {
      const data = await apiGet<Session[]>("/admin/breakglass", { signal });
      setSessions(Array.isArray(data) ? data : []);
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
  async function transition(id: string, verb: "approve" | "revoke") { setWorking(`${verb}:${id}`); setError(null); try { await apiPost(`/admin/breakglass/${id}/${verb}`, {}); await load(); } catch (currentError) { setError(errorMessage(currentError)); } finally { setWorking(null); } }
  const active = useMemo(() => sessions.filter((item) => ["PENDING", "APPROVED"].includes(item.status) && !isExpired(item.expires_at)).length, [sessions]);
  return <div className="page"><section className="hero-row"><div><p className="eyebrow">ADMIN / EMERGENCY ACCESS</p><h1 className="page-title">Break Glass</h1><p className="page-lede">Review exceptional access sessions. Every request expires, requires a second administrator, and leaves an audit record.</p></div><span className="environment-badge"><span className="status-dot status-dot-good" />Admin only</span></section>{error && <div className="inline-alert"><strong>Break-glass action failed</strong><span>{error}</span><button className="text-button" type="button" onClick={() => void load()}>Retry</button></div>}<section className="metric-grid metric-grid-four"><article className="metric-card metric-card-danger"><span>Active sessions</span><strong>{active}</strong><small>Pending or approved and not expired</small></article><article className="metric-card"><span>Total requests</span><strong>{sessions.length}</strong><small>Durable emergency records</small></article><article className="metric-card"><span>Expiry window</span><strong>1h</strong><small>Backend-defined session lifetime</small></article><article className="metric-card"><span>Control model</span><strong>2P</strong><small>Requester cannot approve self</small></article></section><section className="panel warning-panel"><div className="panel-heading"><div><p className="eyebrow">EMERGENCY CONTROL</p><h2>Use only for a documented exception</h2></div></div><p className="panel-note">Break-glass access is not a shortcut around normal permissions. Confirm the reason, affected user, expiry, and second-admin approval before taking action. Revocation remains available while a session is pending or approved.</p></section><section className="panel application-list-panel"><div className="panel-heading"><div><p className="eyebrow">SESSION REGISTER</p><h2>{loading ? "Loading sessions" : `${sessions.length} session${sessions.length === 1 ? "" : "s"}`}</h2></div><button className="secondary-button compact-button" type="button" onClick={() => void load()}>Refresh</button></div>{loading ? <div className="empty-state"><span className="loading-bar" />Loading break-glass sessions…</div> : sessions.length ? <div className="admin-record-list">{sessions.map((session) => <article className="admin-record" key={session.id}><div className="admin-record-main"><div className="admin-record-title"><span className={`decision-badge ${session.status === "APPROVED" ? "badge-warning" : session.status === "REVOKED" || session.status === "EXPIRED" ? "badge-danger" : "badge-neutral"}`}>{session.status}</span><b>User {session.user_id}</b></div><p>{session.reason}</p><small>Requested by {session.requested_by || "unknown"} · {date(session.created_at)} · Expires {date(session.expires_at)}{session.approved_by ? ` · Approved by ${session.approved_by}` : ""}</small></div><div className="admin-record-actions">{session.status === "PENDING" && <button className="secondary-button compact-button" type="button" disabled={working !== null} onClick={() => void transition(session.id, "approve")}>Approve</button>}{["PENDING", "APPROVED"].includes(session.status) && <button className="danger-button" type="button" disabled={working !== null} onClick={() => void transition(session.id, "revoke")}>{working === `revoke:${session.id}` ? "Revoking…" : "Revoke"}</button>}</div></article>)}</div> : <div className="empty-state"><strong>No break-glass sessions</strong><span>Emergency access requests will appear here when created through the controlled admin flow.</span></div>}</section></div>;
}
