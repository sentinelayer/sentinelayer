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

export const Dashboard: React.FC<{ token: string }> = ({ token }) => {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({ total: 0, pending: 0, completed: 0 })

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.get('/api/v1/orders/', {
          headers: { Authorization: `Bearer ${token}` }
        })
        const data = response.data
        setOrders(data)
        const pending = data.filter((o: Order) => o.status === 'pending').length
        const completed = data.filter((o: Order) => o.status === 'completed').length
        setStats({ total: data.length, pending, completed })
      } catch (error) {
        console.error('Failed to fetch orders:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [token])

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
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
      </div>

      <div style={{ marginTop: '1rem', border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
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
