const BASE = process.env.REACT_APP_API_URL || "http://localhost:8005";

export type ApiError = { status: number; message: string };

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("sl_access_token");
  const tenant = localStorage.getItem("sl_tenant_id") || "";
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  if (tenant) h["X-Tenant-ID"] = tenant;
  return h;
}

export async function apiGet<T = unknown>(path: string): Promise<T> {
  const res = await fetch(`\( {BASE} \){path}`, { headers: authHeaders() });
  if (!res.ok) {
    const body = await res.text();
    throw { status: res.status, message: body || res.statusText } as ApiError;
  }
  return res.json() as Promise<T>;
}

export async function apiPost<T = unknown>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`\( {BASE} \){path}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw { status: res.status, message: text || res.statusText } as ApiError;
  }
  return res.json() as Promise<T>;
}

export async function login(email: string, password: string): Promise<{ access_token: string }> {
  const data = await apiPost<{ access_token: string }>("/api/v1/auth/login", { email, password });
  localStorage.setItem("sl_access_token", data.access_token);
  return data;
}

export function logout(): void {
  localStorage.removeItem("sl_access_token");
  localStorage.removeItem("sl_tenant_id");
}
