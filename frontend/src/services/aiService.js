import { api } from './api';

const AI_BASE_URL = '/ai/analytics';

export const aiService = {
  // 1. Get Project Forecast
  getForecast: async (projectId) => {
    try {
      const response = await api.get(`${AI_BASE_URL}/project-forecast/${projectId}/`);
      return response.data;
    } catch (error) {
      console.error("Forecast fetch error:", error);
      return null;
    }
  },

  // 2. Get Burnout Risks
  getBurnoutRisks: async (projectId) => {
    try {
      // Assuming the backend endpoint accepts project ID or we filter by workspace
      // Adjusting endpoint to match your previous backend structure if needed
      const response = await api.get(`${AI_BASE_URL}/burnout-detection/${projectId}/`); 
      return response.data;
    } catch (error) {
      console.error("Burnout fetch error:", error);
      return [];
    }
  },

  // 3. Get Velocity Data
  getVelocity: async (projectId) => {
    try {
      const response = await api.get(`${AI_BASE_URL}/velocity/${projectId}/`);
      return response.data;
    } catch (error) {
      console.error("Velocity fetch error:", error);
      return [];
    }
  },

  // 4. Get Bottlenecks
  getBottlenecks: async (projectId) => {
    try {
      const response = await api.get(`${AI_BASE_URL}/bottlenecks/${projectId}/`);
      return response.data;
    } catch (error) {
      console.error("Bottlenecks fetch error:", error);
      return null;
    }
  },

  // 5. Assign Task (Helper)
  assignTask: async (taskId, userId) => {
    return await api.post(`/tasks/tasks/${taskId}/assign_task/`, { user_id: userId });
  }
};