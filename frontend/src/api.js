import axios from 'axios';

const API_BASE = 'http://localhost:8000';

// Create a shared axios instance
const api = axios.create({ baseURL: API_BASE });

// We store a reference to the logout function so the interceptor can call it
let _logout = null;
let _getToken = null;

export function setupApiInterceptors({ getToken, logout }) {
  _logout = logout;
  _getToken = getToken;
}

// Request interceptor — attach Authorization header
api.interceptors.request.use((config) => {
  const token = _getToken?.();
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — on 401 clear auth and navigate to /login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      _logout?.();
      // Signal the app to redirect to login
      window.dispatchEvent(new CustomEvent('lazarus:unauthorized'));
    }
    return Promise.reject(error);
  }
);

export default api;
