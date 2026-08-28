import React, { useEffect, useState } from "react";
import { api, errorMessage, isAbortError } from "../../api/client";

type GraphNode = { id?: string; name?: string };
type GraphEdge = { id?: string; source?: string; target?: string };
type GraphResponse = { nodes?: GraphNode[]; edges?: GraphEdge[] };

export const AttackGraphPage: React.FC = () => {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    api.get<GraphResponse>("/attack-graph", { signal: controller.signal })
      .then((data) => { setNodes(Array.isArray(data.nodes) ? data.nodes : []); setEdges(Array.isArray(data.edges) ? data.edges : []); setError(null); })
      .catch((currentError) => { if (!isAbortError(currentError)) setError(errorMessage(currentError)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, []);

  if (loading) return <div className="page-state"><span className="loading-bar" />Loading attack graph…</div>;
  if (error) return <div className="page-state page-state-error"><strong>Attack graph unavailable</strong><span>{error}</span></div>;
  return <div className="page attack-graph-page"><h1 className="page-title">Attack Graph</h1><div className="graph-container"><div className="graph-stats"><p>Nodes: {nodes.length}</p><p>Edges: {edges.length}</p></div><div className="graph-visualization">{nodes.length === 0 ? <p>No attack paths detected</p> : <ul>{nodes.map((node, index) => <li key={node.id || index}>{node.name || node.id || "Unnamed node"}</li>)}</ul>}</div></div></div>;
};

export default AttackGraphPage;
