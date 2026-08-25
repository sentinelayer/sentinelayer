import axios from 'axios'

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' }
})

export const login = async (email: string, password: string) => {
  const res = await api.post('/api/v1/auth/login', { email, password })
  return res.data
}

export const getOrders = async (token: string) => {
  const res = await api.get('/api/v1/orders/', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export const createOrder = async (token: string, data: any) => {
  const res = await api.post('/api/v1/orders/', data, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}
