import axios from 'axios';

// Create a dedicated Axios instance
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api', // Django Backend URL
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds
});

// --- Request Interceptor ---
// Automatically injects the JWT token if it exists in localStorage
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// --- Response Interceptor ---
// Handles global errors like 401 (Unauthorized)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // specific check: 401 error and not already retrying
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // TODO: Here we would trigger the Token Refresh flow. 
      // For now, we logout the user to be safe.
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

export default apiClient;