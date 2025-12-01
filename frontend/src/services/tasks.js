// src/api/tasks.js
import apiClient from './client';
import { formatResponse, transformApiError, buildQueryParams, createAbortController } from '@utils/apiHelpers';

export async function getTasks(projectId, filters = {}, { signal } = {}) {
  try {
    const params = buildQueryParams(filters);
    const url = projectId ? `/projects/${projectId}/tasks/` : '/tasks/';
    const res = await apiClient.get(url, { params, signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function getTaskById(id, { signal } = {}) {
  try {
    const res = await apiClient.get(`/tasks/${id}/`, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function createTask(data, { signal } = {}) {
  try {
    const res = await apiClient.post('/tasks/', data, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function updateTask(id, data, { signal } = {}) {
  try {
    const res = await apiClient.patch(`/tasks/${id}/`, data, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function deleteTask(id, { signal } = {}) {
  try {
    const res = await apiClient.delete(`/tasks/${id}/`, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function addComment(taskId, comment, { signal } = {}) {
  try {
    const res = await apiClient.post(`/tasks/${taskId}/comments/`, { comment }, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

// file upload: using multipart/form-data
export async function uploadAttachment(taskId, file, { onUploadProgress, signal } = {}) {
  try {
    const form = new FormData();
    form.append('file', file);
    const res = await apiClient.post(`/tasks/${taskId}/attachments/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
      signal,
    });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function trackTime(taskId, timeEntry = {}, { signal } = {}) {
  try {
    const res = await apiClient.post(`/tasks/${taskId}/time-entries/`, timeEntry, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export function createTasksAbortController() {
  return createAbortController();
}
