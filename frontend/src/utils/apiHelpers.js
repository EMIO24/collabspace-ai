import PropTypes from 'prop-types';



export function transformApiError(error) {
  // axios error
  if (error?.response) {
    const { status, data } = error.response;
    const message =
      (data && (data.detail || data.message || data.error)) ||
      (Array.isArray(data) && data.join(', ')) ||
      error.message ||
      'Request failed';
    return {
      message,
      status,
      details: data || null,
      originalError: error,
    };
  }

  // request made but no response (network)
  if (error?.request) {
    return {
      message: 'No response received from server',
      status: null,
      details: null,
      originalError: error,
    };
  }

  // something else
  return {
    message: error?.message || 'Unknown error',
    status: null,
    details: null,
    originalError: error,
  };
}

/**
 * Format a successful axios response to { data, status, headers }
 */
export function formatResponse(response) {
  if (!response) return { data: null, status: null, headers: null };
  return {
    data: response.data,
    status: response.status,
    headers: response.headers,
  };
}


export function buildQueryParams(params = {}) {
  const clean = {};
  Object.keys(params || {}).forEach((k) => {
    const v = params[k];
    if (v !== undefined && v !== null && v !== '') clean[k] = v;
  });
  return clean;
}


export function createAbortController() {
  if (typeof AbortController !== 'undefined') {
    return new AbortController();
  }
  // Fallback shim (very old browsers) - provide no-op
  return {
    signal: undefined,
    abort: () => {},
  };
}


export const WorkspaceShape = PropTypes.shape({
  id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  name: PropTypes.string,
  slug: PropTypes.string,
  is_public: PropTypes.bool,
  owner: PropTypes.object,
  created_at: PropTypes.string,
});

export const ProjectShape = PropTypes.shape({
  id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  name: PropTypes.string,
  description: PropTypes.string,
  workspace: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  created_at: PropTypes.string,
});

export const TaskShape = PropTypes.shape({
  id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  title: PropTypes.string,
  description: PropTypes.string,
  status: PropTypes.string,
  assignee: PropTypes.object,
  project: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  due_date: PropTypes.string,
});
