const BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
const API_PREFIX = "/api/v1";

export type ApiError = { status: number; message: string; code?: string };
export type RequestOptions = { signal?: AbortSignal };

const SAFE_MESSAGES: Record<number, string> = {
  400: "The request could not be processed.",
  401: "Your session is invalid or has expired. Please sign in again.",
  403: "You do not have permission to perform this action.",
  404: "The requested resource was not found.",
  409: "This action conflicts with the current resource state.",
  422: "Some submitted fields are invalid.",
  429: "Too many requests. Please try again shortly.",
  500: "The service encountered an internal error.",
  502: "The upstream service is temporarily unavailable.",
  503: "The service is temporarily unavailable.",
};

function safeDetail(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  const normalized = value.replace(/[\r\n\t]+/g, " ").trim();
  if (!normalized || normalized.length > 180) return undefined;
  return normalized;
}

async function errorFromResponse(res: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    // Discard non-JSON response bodies; upstream text may contain secrets.
  }
  const payload = body && typeof body === "object" ? body as Record<string, unknown> : {};
  const code = safeDetail(payload.code);
  const detail = safeDetail(payload.detail) || safeDetail(payload.error) || safeDetail(payload.message);
  return { status: res.status, code, message: detail || SAFE_MESSAGES[res.status] || "The request could not be completed." };
}

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

export function errorMessage(error: unknown): string {
  if (isAbortError(error)) return "";
  if (error && typeof error === "object" && "message" in error) {
    const message = (error as { message?: unknown }).message;
    if (typeof message === "string" && message.length <= 180) return message;
  }
  return "The request could not be completed. Please try again.";
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

export async function apiGet<T = unknown>(path: string, options: RequestOptions = {}): Promise<T> {
  const res = await fetch(`${BASE}${apiPath(path)}`, { headers: authHeaders(), signal: options.signal });
  if (!res.ok) throw await errorFromResponse(res);
  return res.json() as Promise<T>;
}

export async function apiPost<T = unknown>(path: string, body: unknown, options: RequestOptions = {}): Promise<T> {
  const res = await fetch(`${BASE}${apiPath(path)}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
    signal: options.signal,
  });
  if (!res.ok) throw await errorFromResponse(res);
  return res.json() as Promise<T>;
}

export async function apiPut<T = unknown>(path: string, body: unknown, options: RequestOptions = {}): Promise<T> {
  const res = await fetch(`${BASE}${apiPath(path)}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(body),
    signal: options.signal,
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
  get: <T = unknown>(path: string, options?: RequestOptions): Promise<T> => apiGet<T>(path, options),
  post: <T = unknown>(path: string, body: unknown, options?: RequestOptions): Promise<T> => apiPost<T>(path, body, options),
  put: <T = unknown>(path: string, body: unknown, options?: RequestOptions): Promise<T> => apiPut<T>(path, body, options),
};
