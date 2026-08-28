export type DashboardRole = "viewer" | "analyst" | "operator" | "admin" | "owner";

function tokenClaims(): Record<string, unknown> {
  const token = localStorage.getItem("sl_access_token");
  if (!token) return {};
  try {
    const encoded = token.split(".")[1];
    if (!encoded) return {};
    return JSON.parse(atob(encoded.replace(/-/g, "+").replace(/_/g, "/"))) as Record<string, unknown>;
  } catch {
    return {};
  }
}

export function currentRole(): DashboardRole {
  const claims = tokenClaims();
  const value = String(claims.role || claims.user_role || claims["https://sentinellayer.dev/role"] || "viewer").toLowerCase();
  if (["owner", "admin", "operator", "analyst"].includes(value)) return value as DashboardRole;
  return "viewer";
}

export function canMutate(): boolean {
  return currentRole() !== "viewer";
}

export function roleLabel(): string {
  const role = currentRole();
  return role.charAt(0).toUpperCase() + role.slice(1);
}
