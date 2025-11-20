import axios from 'axios';
import { transformApiError } from '@utils/apiHelpers';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// --- Configuration ---
const PUBLIC_PATHS = [
  '/auth/login/',
  '/auth/register/',
  '/auth/refresh/',
  '/auth/register',
  '/auth/reset-password',
    '/status',
];

// Create the primary axios instance used for all API requests (Token is added via interceptor)
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  timeout: 30000, // 30s default
});

// A separate axios instance without interceptors for specific unauthenticated calls 
// (Used primarily for the token refresh call itself to avoid interceptor recursion)
const plainClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// --- Token Refresh Orchestration (Concurrency Handling) ---
let isRefreshing = false;
let refreshSubscribers = [];

function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb);
}

function onRefreshed(newToken) {
  refreshSubscribers.forEach((cb) => cb(newToken));
  refreshSubscribers = [];
}

// --- Request Interceptor: Conditional Token Attachment ---
apiClient.interceptors.request.use(
  (config) => {
    // 1. Check if the current request path is one of the PUBLIC_PATHS
    const isPublic = PUBLIC_PATHS.some(path => config.url?.endsWith(path));

    if (isPublic) {
      // For public paths, explicitly delete any potentially stale Authorization header
      delete config.headers.Authorization;
      return config;
    }

    // 2. For protected paths, add the access token if available
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// --- Response Interceptor: Handle 401 Unauthorized & Token Refresh ---
apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;

    // Handle network errors (no response)
    if (!error.response) {
      return Promise.reject(transformApiError(error));
    }

    const status = error.response.status;
    const isRefreshPath = originalRequest.url?.endsWith('/auth/refresh/');

    // Condition to attempt refresh: 401 status, not already retried, AND not the refresh call itself
    if (status === 401 && !originalRequest._retry && !isRefreshPath) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');

      // 1. Handle Missing Refresh Token (Force Logout)
      if (!refreshToken) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(transformApiError(error));
      }

      // 2. Handle Concurrent Refresh Requests (Queueing)
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh((token) => {
            if (!token) return reject(transformApiError(error));
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(apiClient(originalRequest));
          });
        });
      }

      // 3. Perform Refresh
      isRefreshing = true;

      try {
        // Use plainClient for the refresh request
        const resp = await plainClient.post('/auth/refresh/', { refresh: refreshToken });

        const newAccess = resp.data?.access;
        const newRefresh = resp.data?.refresh || refreshToken;

        if (!newAccess) throw new Error('Refresh failed, no new access token.');

        // Update tokens
        localStorage.setItem('access_token', newAccess);
        if (newRefresh) localStorage.setItem('refresh_token', newRefresh);
        apiClient.defaults.headers.common.Authorization = `Bearer ${newAccess}`;

        // Notify queued requests and finish refreshing state
        isRefreshing = false;
        onRefreshed(newAccess);

        // Retry original request
        originalRequest.headers.Authorization = `Bearer ${newAccess}`;
        return apiClient(originalRequest);

      } catch (refreshError) {
        // Handle all refresh failures
        isRefreshing = false;
        onRefreshed(null); 
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(transformApiError(refreshError));
      }
    }

    // For all other errors
    return Promise.reject(transformApiError(error));
  }
);

export default apiClient;
export { plainClient, BASE_URL };