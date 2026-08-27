import React, { useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { apiGet, logout } from "../api/client";

interface LayoutProps {
  children: React.ReactNode;
}

type NavItem = { to: string; label: string; code: string };
type NavGroup = { label: string; items: NavItem[] };
type CurrentUser = { email?: string; full_name?: string; tenant_id?: string; is_admin?: boolean; mfa_enabled?: boolean };

const NAV_GROUPS: NavGroup[] = [
  {
    label: "Workspace",
    items: [{ to: "/", label: "Overview", code: "OV" }],
  },
  {
    label: "Protect",
    items: [
      { to: "/applications", label: "Applications", code: "AP" },
      { to: "/live-protection", label: "Live Protection", code: "LP" },
    ],
  },
  {
    label: "Detect",
    items: [
      { to: "/events", label: "Events", code: "EV" },
      { to: "/alerts", label: "Alerts", code: "AL" },
      { to: "/incidents", label: "Incidents", code: "IN" },
      { to: "/risk", label: "Risk", code: "RK" },
      { to: "/user-risk", label: "User Risk", code: "UR" },
      { to: "/attack-graph", label: "Attack Graph", code: "AG" },
    ],
  },
  {
    label: "Investigate",
    items: [
      { to: "/explainability", label: "Explainability", code: "EX" },
      { to: "/evidence", label: "Evidence", code: "ED" },
      { to: "/heatmap", label: "Heatmap", code: "HM" },
    ],
  },
  {
    label: "Govern",
    items: [
      { to: "/policies", label: "Policies", code: "PL" },
      { to: "/configuration", label: "Configuration", code: "CF" },
      { to: "/sla", label: "SLA", code: "SL" },
    ],
  },
];

const ADMIN_ITEMS: NavItem[] = [
  { to: "/admin/break-glass", label: "Break Glass", code: "BG" },
  { to: "/admin/high-risk-actions", label: "High-risk actions", code: "HR" },
];

function readAdminClaim(): boolean {
  try {
    const token = localStorage.getItem("sl_access_token");
    if (!token) return false;
    const payload = JSON.parse(atob(token.split(".")[1])) as { is_admin?: boolean };
    return payload.is_admin === true;
  } catch {
    return false;
  }
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const isAdmin = useMemo(readAdminClaim, []);

  React.useEffect(() => {
    let cancelled = false;
    apiGet<CurrentUser>("/auth/me").then((currentUser) => {
      if (!cancelled) setUser(currentUser);
    }).catch(() => {
      // Navigation remains usable when the optional profile lookup is unavailable.
    });
    return () => { cancelled = true; };
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isActive = (to: string) => to === "/" ? location.pathname === "/" : location.pathname === to || location.pathname.startsWith(`${to}/`);

  return (
    <div className="app-shell">
      <button className="mobile-nav-toggle" type="button" aria-label="Toggle navigation" onClick={() => setMobileOpen((open) => !open)}>
        <span />
        <span />
        <span />
      </button>
      {mobileOpen && <button className="mobile-nav-backdrop" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true">SL</div>
          <div>
            <strong>SentinelLayer</strong>
            <span>Security control plane</span>
          </div>
        </div>
        <div className="workspace-switcher" aria-label="Current workspace">
          <span className="workspace-dot" />
          <span><b>{user?.tenant_id ? `Workspace ${user.tenant_id.slice(0, 8)}` : "Current workspace"}</b><small>Production · tenant-scoped</small></span>
          <span className="chevron">⌄</span>
        </div>
        <nav className="side-nav" aria-label="Primary navigation">
          {NAV_GROUPS.map((group) => (
            <div className="nav-group" key={group.label}>
              <p>{group.label}</p>
              {group.items.map((item) => (
                <Link key={item.to} to={item.to} className={`nav-link ${isActive(item.to) ? "nav-link-active" : ""}`} onClick={() => setMobileOpen(false)}>
                  <span className="nav-code">{item.code}</span>
                  <span>{item.label}</span>
                </Link>
              ))}
            </div>
          ))}
          {isAdmin && (
            <div className="nav-group">
              <p>Administration</p>
              {ADMIN_ITEMS.map((item) => (
                <Link key={item.to} to={item.to} className={`nav-link ${isActive(item.to) ? "nav-link-active" : ""}`} onClick={() => setMobileOpen(false)}>
                  <span className="nav-code">{item.code}</span>
                  <span>{item.label}</span>
                </Link>
              ))}
            </div>
          )}
        </nav>
        <div className="sidebar-footer">
          <div className="runtime-status"><span className="status-dot status-dot-good" /><span><b>Runtime operational</b><small>Last check just now</small></span></div>
          <button className="logout-button" type="button" onClick={handleLogout}>Sign out</button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb"><span className="breadcrumb-muted">SentinelLayer</span><span>/</span><strong>{location.pathname === "/" ? "Overview" : location.pathname.split("/").filter(Boolean).pop()?.replace(/-/g, " ")}</strong></div>
          <div className="topbar-actions"><span className="environment-badge"><span className="status-dot status-dot-good" />Production</span><span className="user-pill"><span className="user-avatar">{(user?.full_name || user?.email || "S").slice(0, 1).toUpperCase()}</span><span><b>{user?.full_name || user?.email || "Session user"}</b><small>{user?.is_admin || isAdmin ? "Administrator" : "Viewer"}</small></span></span><button className="topbar-button" type="button" aria-label="Open notifications">Notifications <span className="notification-count">0</span></button></div>
        </header>
        <main className="content-area">{children}</main>
      </div>
    </div>
  );
};

export default Layout;

/* Keep a named export for older imports. */
export { NAV_GROUPS };
