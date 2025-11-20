import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api';

// Paths that do NOT require an Authorization header
const UNAUTHENTICATED_PATHS = ['/login', '/register', '/reset-password', '/status'];

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach auth token to outgoing requests
api.interceptors.request.use((config) => {
  const { url } = config;
  
  // Check if the request targets an unauthenticated path
  const isAuthPath = UNAUTHENTICATED_PATHS.some(path => url.includes(path));

  if (isAuthPath) {
    // Skip token attachment for public routes
    return config;
  }
  
  try {
    // Retrieve token from storage
    const token = localStorage.getItem('authToken'); 
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch (err) {
    // Log token retrieval errors but allow the request to proceed (without the token)
    console.error('Failed to retrieve auth token:', err);
  }
  
  return config;
}, (error) => Promise.reject(error));

export default api;