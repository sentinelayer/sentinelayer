import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const login = async (email: string, password: string) => {
  const response = await api.post('/api/v1/auth/login', { email, password });
  return response.data;
};

export const getOrders = async (token: string) => {
  const response = await api.get('/api/v1/orders/', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const createOrder = async (token: string, data: any) => {
  const response = await api.post('/api/v1/orders/', data, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export default api;
