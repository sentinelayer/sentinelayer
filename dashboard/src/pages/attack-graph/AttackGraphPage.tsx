import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'

export const AttackGraphPage: React.FC = () => {
    const [nodes, setNodes] = useState([])
    const [edges, setEdges] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.get('/attack-graph')
            .then(data => { setNodes(data.nodes || []); setEdges(data.edges || []); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="attack-graph-page">
            <h1>Attack Graph</h1>
            <div className="graph-container">
                <div className="graph-stats">
                    <p>Nodes: {nodes.length}</p>
                    <p>Edges: {edges.length}</p>
                </div>
                <div className="graph-visualization">
                    {nodes.length === 0 ? (
                        <p>No attack paths detected</p>
                    ) : (
                        <ul>
                            {nodes.map((n: any, i: number) => (
                                <li key={i}>{n.name || n.id}</li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
        </div>
    )
}
