import axios, { AxiosError, AxiosResponse } from 'axios';
import { ApiError } from '@/types/api';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('cliniq_access_token');
  if (token && token !== 'undefined') {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('cliniq_access_token');
      localStorage.removeItem('cliniq_refresh_token');
      window.dispatchEvent(new Event('cliniq_unauthorized'));
      
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        window.location.href = '/login';
      }
    }

    const apiError: ApiError = {
      message: (error.response?.data as any)?.message || error.message || 'An unexpected error occurred',
      status: error.response?.status,
      code: (error.response?.data as any)?.code,
    };

    return Promise.reject(apiError);
  }
);

export default client;
