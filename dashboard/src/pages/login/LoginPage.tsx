import React, { useState } from "react";
import { errorMessage, login, register } from "../../api/client";

export default function LoginPage({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [bootstrapToken, setBootstrapToken] = useState("");
  const [tenantId] = useState<string>(() => crypto.randomUUID());
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function switchMode(nextMode: "login" | "register") {
    setMode(nextMode);
    setError(null);
  }

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        await register(email.trim(), password, fullName.trim(), tenantId, bootstrapToken);
      }
      await login(email.trim(), password);
      onSuccess();
    } catch (err: unknown) {
      const message = errorMessage(err);
      if (message) setError(message);
    } finally {
      setLoading(false);
    }
  }

  const isRegister = mode === "register";

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="auth-title">
        <div className="auth-brand" aria-hidden="true">SL</div>
        <p className="eyebrow">SENTINELLAYER CONTROL PLANE</p>
        <h1 id="auth-title">{isRegister ? "Create your workspace" : "Welcome back"}</h1>
        <p className="auth-subtitle">
          {isRegister
            ? "Create a secure tenant workspace to start monitoring your applications."
            : "Sign in to continue to your security workspace."}
        </p>

        <form className="auth-form" onSubmit={submit}>
          {isRegister && (
            <label>
              Full name
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                autoComplete="name"
                placeholder="Your name"
                required
              />
              <span className="field-help">A new workspace ID will be generated automatically.</span>
            </label>
          )}
          <label>
            Email address
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              placeholder="you@example.com"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={isRegister ? "new-password" : "current-password"}
              placeholder="At least 12 characters"
              minLength={12}
              required
            />
            <span className="field-help">Use at least 12 characters.</span>
          </label>

          {isRegister && (
            <label>
              Bootstrap admin token <span className="muted">(optional)</span>
              <input
                type="password"
                value={bootstrapToken}
                onChange={(e) => setBootstrapToken(e.target.value)}
                autoComplete="off"
                placeholder="Only for initial admin setup"
              />
              <span className="field-help">Use this only if your organization configured first-admin onboarding.</span>
            </label>
          )}

          {error && <p className="auth-error" role="alert">{error}</p>}

          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "Please wait…" : isRegister ? "Create account" : "Sign in"}
          </button>
        </form>

        <div className="auth-switch">
          <span>{isRegister ? "Already have an account?" : "New to SentinelLayer?"}</span>
          <button type="button" className="text-button" onClick={() => switchMode(isRegister ? "login" : "register")}>
            {isRegister ? "Sign in" : "Create an account"}
          </button>
        </div>
      </section>
    </main>
  );
}
