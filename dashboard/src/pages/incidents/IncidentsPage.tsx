import React, { useEffect, useState } from "react";
import { apiGet, apiPost, ApiError } from "../../api/client";

type Incident = { id: string; severity: string; status: string };

export default function IncidentsPage() {
  const [items, setItems] = useState<Incident[]>([]);
  const [severity, setSeverity] = useState("medium");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setItems(await apiGet<Incident[]>("/api/v1/incidents"));
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
      await apiPost("/api/v1/incidents", { severity, description });
      setDescription("");
      await load();
    } catch (err) {
      setError((err as ApiError).message);
    }
  }

  return (
    <div className="page">
      <h1>Incidents</h1>
      {error && <p className="error">{error}</p>}
      <form onSubmit={create}>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
          <option value="critical">critical</option>
        </select>
        <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" required />
        <button type="submit">Open incident</button>
      </form>
      <ul>
        {items.map((i) => (
          <li key={i.id}>{i.severity} — {i.status} <code>{i.id}</code></li>
        ))}
      </ul>
    </div>
  );
}
