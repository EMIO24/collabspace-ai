import apiClient, { BASE_URL } from './client';
import { plainClient } from './client';
import { formatResponse, transformApiError, createAbortController } from '@utils/apiHelpers';

/**
 * Authentication related API calls
 */

export async function login(email, password, { signal } = {}) {
  try {
    const res = await apiClient.post('/auth/login/', { email, password }, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function register(userData, { signal } = {}) {
  try {
    const res = await apiClient.post('/auth/register/', userData, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function refreshToken(refreshToken, { signal } = {}) {
  try {
    // use plainClient to avoid interceptor loops
    const res = await plainClient.post('/auth/refresh/', { refresh: refreshToken }, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function logout({ signal } = {}) {
  try {
    const res = await apiClient.post('/auth/logout/', null, { signal });
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    return formatResponse(res);
  } catch (err) {
    // still clear tokens if logout fails
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    throw transformApiError(err);
  }
}

export async function verifyEmail(token, { signal } = {}) {
  try {
    const res = await apiClient.post('/auth/verify-email/', { token }, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function requestPasswordReset(email, { signal } = {}) {
  try {
    const res = await apiClient.post('/auth/password/reset/', { email }, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function confirmPasswordReset(token, newPassword, { signal } = {}) {
  try {
    const res = await apiClient.post('/auth/password/reset/confirm/', {
      token,
      password: newPassword,
    }, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function setup2FA({ signal } = {}) {
  try {
    const res = await apiClient.post('/auth/2fa/setup/', null, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function verify2FA(code, { signal } = {}) {
  try {
    const res = await apiClient.post('/auth/2fa/verify/', { code }, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

// convenience factory to create controller + call
export function createAuthAbortController() {
  return createAbortController();
}
