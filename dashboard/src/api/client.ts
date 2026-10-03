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

const SAFE_CODE_MESSAGES: Record<string, string> = {
  INVALID_CREDENTIALS: "The email or password is incorrect.",
  INVALID_API_KEY: "The API key is invalid or expired.",
  MFA_REQUIRED: "Multi-factor authentication is required.",
  MFA_INVALID: "The multi-factor authentication code is invalid.",
  FORBIDDEN: "You do not have permission to perform this action.",
  RATE_LIMITED: "Too many requests. Please try again shortly.",
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
  const rawCode = safeDetail(payload.code)?.toUpperCase();
  const code = rawCode && /^[A-Z][A-Z0-9_]{1,63}$/.test(rawCode) ? rawCode : undefined;
  return { status: res.status, code, message: (code && SAFE_CODE_MESSAGES[code]) || SAFE_MESSAGES[res.status] || "The request could not be completed." };
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

export type LoginResponse = { access_token: string; mfa_required?: boolean };

async function publicPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${apiPath(path)}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  if (!res.ok) throw await errorFromResponse(res);
  return res.json() as Promise<T>;
}

export async function login(email: string, password: string, mfaCode?: string): Promise<LoginResponse> {
  const body: Record<string, string> = { email, password };
  if (mfaCode?.trim()) body.mfa_code = mfaCode.trim();
  const data = await publicPost<LoginResponse>("/auth/login", body);
  if (data.mfa_required) {
    logout();
    return data;
  }
  if (!data.access_token) throw { status: 401, message: "Sign-in did not complete. Please try again." };
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
  const body: Record<string, string> = { email, password, full_name, tenant_id };
  if (bootstrap_token?.trim()) body.bootstrap_token = bootstrap_token.trim();
  return publicPost("/auth/register", body);
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
