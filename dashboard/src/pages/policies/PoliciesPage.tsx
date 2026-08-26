import React, { useEffect, useState } from "react";
import { apiGet, apiPost, ApiError } from "../../api/client";

type Policy = { id: string; name: string; tenant_id?: string };

export default function PoliciesPage() {
  const [items, setItems] = useState<Policy[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setItems(await apiGet<Policy[]>("/api/v1/policies"));
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
      await apiPost("/api/v1/policies", { name, rules: { mode: "default" } });
      setName("");
      await load();
    } catch (err) {
      setError((err as ApiError).message);
    }
  }

  return (
    <div className="page">
      <h1>Policies</h1>
      {error && <p className="error">{error}</p>}
      <form onSubmit={create}>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Policy name" required />
        <button type="submit">Create</button>
      </form>
      <ul>
        {items.map((p) => (
          <li key={p.id}>{p.name} <code>{p.id}</code></li>
        ))}
      </ul>
    </div>
  );
}
