const BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
const API_PREFIX = "/api/v1";

export type ApiError = { status: number; message: string };

async function errorFromResponse(res: Response): Promise<ApiError> {
  const raw = await res.text();
  let message = raw || res.statusText;
  try {
    const body = JSON.parse(raw) as { detail?: string; error?: string; message?: string };
    message = body.detail || body.error || body.message || message;
  } catch {
    // Keep the plain response when the backend does not return JSON.
  }
  return { status: res.status, message };
}

function apiPath(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return normalized === API_PREFIX || normalized.startsWith(`${API_PREFIX}/`)
    ? normalized
    : `${API_PREFIX}${normalized}`;
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("sl_access_token");
  const tenant = localStorage.getItem("sl_tenant_id") || "";
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  if (tenant) h["X-Tenant-ID"] = tenant;
  return h;
}

export async function apiGet<T = unknown>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${apiPath(path)}`, { headers: authHeaders() });
  if (!res.ok) throw await errorFromResponse(res);
  return res.json() as Promise<T>;
}

export async function apiPost<T = unknown>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${apiPath(path)}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await errorFromResponse(res);
  return res.json() as Promise<T>;
}

export async function login(email: string, password: string): Promise<{ access_token: string }> {
  const data = await apiPost<{ access_token: string }>("/auth/login", { email, password });
  if (data.access_token) {
    localStorage.setItem("sl_access_token", data.access_token);
    try {
      const payload = JSON.parse(atob(data.access_token.split(".")[1]));
      if (payload.tenant_id) localStorage.setItem("sl_tenant_id", payload.tenant_id);
    } catch {
      // Token validation remains server-side; payload decoding only supplies tenant context.
    }
  }
  return data;
}

export async function register(
  email: string,
  password: string,
  full_name: string,
  tenant_id: string,
  bootstrap_token?: string
): Promise<unknown> {
  localStorage.setItem("sl_tenant_id", tenant_id);
  const body: Record<string, string> = { email, password, full_name, tenant_id };
  if (bootstrap_token?.trim()) body.bootstrap_token = bootstrap_token.trim();
  return apiPost("/auth/register", body);
}

export function logout(): void {
  localStorage.removeItem("sl_access_token");
  localStorage.removeItem("sl_tenant_id");
}

export function isLoggedIn(): boolean {
  return !!localStorage.getItem("sl_access_token");
}

export const api = {
  get: <T = unknown>(path: string): Promise<T> => apiGet<T>(path),
  post: <T = unknown>(path: string, body: unknown): Promise<T> => apiPost<T>(path, body),
};
