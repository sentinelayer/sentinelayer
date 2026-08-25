import React, { useState, useEffect } from 'react'
import { api } from '../api/client'

interface Order {
  id: string
  product_id: string
  quantity: number
  total_amount: number
  status: string
  created_at: string
}

interface SecurityStatus {
  waf: string
  rate_limit: string
  auth: string
  tenant: string
}

export const Dashboard: React.FC<{ token: string }> = ({ token }) => {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({ total: 0, pending: 0, completed: 0 })
  const [security, setSecurity] = useState<SecurityStatus | null>(null)
  const [risk, setRisk] = useState<any>(null)
  const [behavior, setBehavior] = useState<any>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const headers = { Authorization: `Bearer ${token}` }
        
        const [ordersRes, securityRes, riskRes, behaviorRes] = await Promise.all([
          api.get('/api/v1/orders/', { headers }),
          api.get('/api/v1/dashboard/security', { headers }).catch(() => ({ data: null })),
          api.get('/api/v1/risk/calculate', { headers }).catch(() => ({ data: null })),
          api.get('/api/v1/behavior/stats', { headers }).catch(() => ({ data: null }))
        ])
        
        const data = ordersRes.data
        setOrders(data)
        const pending = data.filter((o: Order) => o.status === 'pending').length
        const completed = data.filter((o: Order) => o.status === 'completed').length
        setStats({ total: data.length, pending, completed })
        
        if (securityRes.data) setSecurity(securityRes.data)
        if (riskRes.data) setRisk(riskRes.data)
        if (behaviorRes.data) setBehavior(behaviorRes.data)
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [token])

  if (loading) return <div>Loading...</div>

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
        <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
          <h4>Total Orders</h4>
          <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.total}</p>
        </div>
        <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
          <h4>Pending</h4>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: 'orange' }}>{stats.pending}</p>
        </div>
        <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
          <h4>Completed</h4>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: 'green' }}>{stats.completed}</p>
        </div>
        <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
          <h4>Risk Score</h4>
          <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{risk?.score || 0}</p>
        </div>
      </div>

      {security && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
          <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
            <h4>WAF</h4>
            <p style={{ color: security.waf === 'active' ? 'green' : 'red' }}>{security.waf}</p>
          </div>
          <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
            <h4>Rate Limit</h4>
            <p style={{ color: security.rate_limit === 'active' ? 'green' : 'red' }}>{security.rate_limit}</p>
          </div>
          <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
            <h4>Auth</h4>
            <p style={{ color: security.auth === 'active' ? 'green' : 'red' }}>{security.auth}</p>
          </div>
          <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
            <h4>Tenant</h4>
            <p style={{ color: security.tenant === 'active' ? 'green' : 'red' }}>{security.tenant}</p>
          </div>
        </div>
      )}

      <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
        <h4>Recent Orders</h4>
        <ul>
          {orders.slice(0, 10).map((order) => (
            <li key={order.id}>
              {order.product_id} - {order.quantity}x - ${order.total_amount} - {order.status}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
