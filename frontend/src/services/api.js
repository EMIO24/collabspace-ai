import axios from 'axios';

// Simple Event Emitter for Auth/Maintenance triggers
export const NetworkEvents = {
  listeners: {},
  on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
  },
  emit(event, data) {
    if (this.listeners[event]) this.listeners[event].forEach(cb => cb(data));
  }
};

const BASE_URL = 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response ? error.response.status : null;

    if (status === 401) {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('user');
      NetworkEvents.emit('UNAUTHORIZED');
    }

    if (status === 503) {
      NetworkEvents.emit('MAINTENANCE_MODE');
    }

    return Promise.reject(error);
  }
);