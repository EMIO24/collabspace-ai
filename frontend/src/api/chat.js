import apiClient from './client';
import { formatResponse, transformApiError, buildQueryParams, createAbortController } from '@utils/apiHelpers';

export async function getChannels(workspaceId, { signal } = {}) {
  try {
    const res = await apiClient.get(`/workspaces/${workspaceId}/channels/`, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function getMessages(channelId, page = 1, { signal } = {}) {
  try {
    const params = buildQueryParams({ page });
    const res = await apiClient.get(`/channels/${channelId}/messages/`, { params, signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function sendMessage(channelId, content, { signal } = {}) {
  try {
    const res = await apiClient.post(`/channels/${channelId}/messages/`, { content }, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function addReaction(messageId, emoji, { signal } = {}) {
  try {
    const res = await apiClient.post(`/messages/${messageId}/reactions/`, { emoji }, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export async function getDirectMessages({ signal } = {}) {
  try {
    const res = await apiClient.get(`/messages/direct/`, { signal });
    return formatResponse(res);
  } catch (err) {
    throw transformApiError(err);
  }
}

export function createChatAbortController() {
  return createAbortController();
}
