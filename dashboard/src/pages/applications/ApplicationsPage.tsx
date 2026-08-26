import React, { useEffect, useState } from "react";
import { apiGet, apiPost, ApiError } from "../../api/client";

type App = { id: string; name: string; tenant_id?: string };

export default function ApplicationsPage() {
  const [apps, setApps] = useState<App[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const data = await apiGet<App[]>("/api/v1/applications");
      setApps(Array.isArray(data) ? data : []);
      setError(null);
    } catch (e) {
      setError((e as ApiError).message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    try {
      await apiPost("/api/v1/applications", { name, environment: "production" });
      setName("");
      await load();
    } catch (err) {
      setError((err as ApiError).message);
    }
  }

  return (
    <div className="page">
      <h1>Applications</h1>
      {error && <p className="error">{error}</p>}
      <form onSubmit={create}>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="App name" required />
        <button type="submit">Create</button>
      </form>
      <ul>
        {apps.map((a) => (
          <li key={a.id}>{a.name} <code>{a.id}</code></li>
        ))}
      </ul>
    </div>
  );
}
