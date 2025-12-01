import apiClient from './client';
import { formatResponse, transformApiError, createAbortController } from '@utils/apiHelpers';

/**
 * AI endpoints for CollabSpace AI features
 */

export async function chatCompletion(messages = [], { signal } = {}) {
  try {
    const res = await apiClient.post('/ai/chat/completions/', { messages }, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function analyzeTask(taskId, { signal } = {}) {
  try {
    const res = await apiClient.post(`/ai/tasks/${taskId}/analyze/`, null, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function summarizeMeeting(transcript, { signal } = {}) {
  try {
    const res = await apiClient.post('/ai/summarize/meeting/', { transcript }, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function reviewCode(code, { signal } = {}) {
  try {
    const res = await apiClient.post('/ai/code/review/', { code }, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function getAnalyticsInsights(workspaceId, { signal } = {}) {
  try {
    const res = await apiClient.get(`/workspaces/${workspaceId}/ai/insights/`, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export function createAIApiAbortController() {
  return createAbortController();
}
