import React, { useState } from "react";
import { login, register } from "../../api/client";

export default function LoginPage({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tenantId, setTenantId] = useState<string>(() => crypto.randomUUID());
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        await register(email, password, email.split("@")[0], tenantId);
      }
      await login(email, password);
      onSuccess();
    } catch (err: any) {
      setError(err?.message || "Auth failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page" style={{ maxWidth: 420, margin: "4rem auto" }}>
      <h1>SentinelLayer</h1>
      <p>{mode === "login" ? "Sign in" : "Create tenant account"}</p>
      <form onSubmit={submit}>
        {mode === "register" && (
          <label>
            Tenant ID
            <input value={tenantId} onChange={(e) => setTenantId(e.target.value)} required />
          </label>
        )}
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Password (min 12)
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={12} required />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading}>{loading ? "…" : mode === "login" ? "Login" : "Register"}</button>
      </form>
      <button type="button" onClick={() => setMode(mode === "login" ? "register" : "login")}>
        {mode === "login" ? "Need an account? Register" : "Have an account? Login"}
      </button>
    </div>
  );
}
