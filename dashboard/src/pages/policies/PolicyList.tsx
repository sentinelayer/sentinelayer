import React, { useEffect, useState } from 'react'

interface Policy {
  id: string
  name: string
}

export const PolicyList: React.FC = () => {
  const [policies, setPolicies] = useState<Policy[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPolicies = async () => {
      try {
        const res = await fetch('/api/v1/policies')
        const data = await res.json()
        setPolicies(data)
      } catch (e) {
        console.error('Failed to fetch policies:', e)
      } finally {
        setLoading(false)
      }
    }
    fetchPolicies()
  }, [])

  if (loading) return <div>Loading policies...</div>

  return (
    <div className="policy-list">
      <h1>Policies</h1>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
          </tr>
        </thead>
        <tbody>
          {policies.map((policy) => (
            <tr key={policy.id}>
              <td>{policy.id}</td>
              <td>{policy.name}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
