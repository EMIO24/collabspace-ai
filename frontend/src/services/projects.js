import apiClient from './client';
import { formatResponse, transformApiError, buildQueryParams, createAbortController } from '@utils/apiHelpers';

export async function getProjects(workspaceId, filters = {}, { signal } = {}) {
  try {
    const params = buildQueryParams(filters);
    const url = workspaceId ? `/workspaces/${workspaceId}/projects/` : '/projects/';
    const res = await apiClient.get(url, { params, signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function getProjectById(id, { signal } = {}) {
  try {
    const res = await apiClient.get(`/projects/${id}/`, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function createProject(workspaceId, data, { signal } = {}) {
  try {
    const res = await apiClient.post(`/workspaces/${workspaceId}/projects/`, data, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function updateProject(id, data, { signal } = {}) {
  try {
    const res = await apiClient.patch(`/projects/${id}/`, data, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function deleteProject(id, { signal } = {}) {
  try {
    const res = await apiClient.delete(`/projects/${id}/`, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function getProjectTasks(projectId, { signal } = {}) {
  try {
    const res = await apiClient.get(`/projects/${projectId}/tasks/`, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export function createProjectsAbortController() {
  return createAbortController();
}
