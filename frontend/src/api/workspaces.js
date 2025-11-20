import apiClient from './client';
import { formatResponse, transformApiError, buildQueryParams, createAbortController } from '@utils/apiHelpers';

export async function getWorkspaces(params = {}, { signal } = {}) {
  try {
    const cleanParams = buildQueryParams(params);
    const res = await apiClient.get('/workspaces/', { params: cleanParams, signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function getWorkspaceById(id, { signal } = {}) {
  try {
    const res = await apiClient.get(`/workspaces/${id}/`, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function createWorkspace(data, { signal } = {}) {
  try {
    const res = await apiClient.post('/workspaces/', data, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function updateWorkspace(id, data, { signal } = {}) {
  try {
    const res = await apiClient.patch(`/workspaces/${id}/`, data, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function deleteWorkspace(id, { signal } = {}) {
  try {
    const res = await apiClient.delete(`/workspaces/${id}/`, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function inviteMembers(workspaceId, emails = [], { signal } = {}) {
  try {
    const res = await apiClient.post(`/workspaces/${workspaceId}/invite/`, { emails }, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function getWorkspaceMembers(workspaceId, { signal } = {}) {
  try {
    const res = await apiClient.get(`/workspaces/${workspaceId}/members/`, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export function createWorkspaceAbortController() {
  return createAbortController();
}
