// src/services/authService.js
import api from './api';

const authService = {
  /**
   * Logs the user in and stores tokens.
   * Expected Backend Response: { access: "...", refresh: "...", user: { ... } }
   */
  login: async (email, password) => {
    const response = await api.post('/auth/login/', { email, password });
    
    if (response.data.access && response.data.refresh) {
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
    }
    
    return response.data;
  },

  /**
   * Registers a new user.
   */
  register: async (userData) => {
    const response = await api.post('/auth/register/', userData);
    return response.data;
  },

  /**
   * Refreshes the access token using the refresh token.
   * Note: This manually grabs the refresh token from storage.
   */
  refreshToken: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await api.post('/auth/refresh/', { 
      refresh: refreshToken 
    });

    if (response.data.access) {
      localStorage.setItem('access_token', response.data.access);
    }
    
    return response.data;
  },

  /**
   * Utility to clear session (Logout)
   */
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  }
};

export default authService;