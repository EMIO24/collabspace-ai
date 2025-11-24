import { useState, useCallback } from 'react';
import { chatCompletion, analyzeTask, generateInsights } from '../api/ai';

export function useAI() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [usage, setUsage] = useState({
    used: 0,
    limit: 100,
    resetDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
  });

  const chat = useCallback(async (messages) => {
    setLoading(true);
    setError(null);

    try {
      const response = await chatCompletion(messages);
      setUsage((prev) => ({
        ...prev,
        used: prev.used + 1,
      }));
      return response.data;
    } catch (err) {
      setError(err.message || 'Failed to get AI response');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const analyzeTaskWithAI = useCallback(async (taskData) => {
    setLoading(true);
    setError(null);

    try {
      const response = await analyzeTask(taskData);
      setUsage((prev) => ({
        ...prev,
        used: prev.used + 1,
      }));
      return response.data;
    } catch (err) {
      setError(err.message || 'Failed to analyze task');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getInsights = useCallback(async (dataType, data) => {
    setLoading(true);
    setError(null);

    try {
      const response = await generateInsights(dataType, data);
      setUsage((prev) => ({
        ...prev,
        used: prev.used + 1,
      }));
      return response.data;
    } catch (err) {
      setError(err.message || 'Failed to generate insights');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const generateMeetingNotes = useCallback(async (transcript) => {
    setLoading(true);
    setError(null);

    try {
      const messages = [
        {
          role: 'system',
          content: 'You are a helpful assistant that generates structured meeting notes.',
        },
        {
          role: 'user',
          content: `Please create structured meeting notes from this transcript:\n\n${transcript}\n\nInclude: Summary, Key Points, Action Items, and Decisions.`,
        },
      ];

      const response = await chatCompletion(messages);
      setUsage((prev) => ({
        ...prev,
        used: prev.used + 1,
      }));
      return response.data;
    } catch (err) {
      setError(err.message || 'Failed to generate meeting notes');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const reviewCode = useCallback(async (code, language) => {
    setLoading(true);
    setError(null);

    try {
      const messages = [
        {
          role: 'system',
          content: 'You are an expert code reviewer. Provide constructive feedback on code quality, potential bugs, and improvements.',
        },
        {
          role: 'user',
          content: `Please review this ${language} code:\n\n\`\`\`${language}\n${code}\n\`\`\``,
        },
      ];

      const response = await chatCompletion(messages);
      setUsage((prev) => ({
        ...prev,
        used: prev.used + 1,
      }));
      return response.data;
    } catch (err) {
      setError(err.message || 'Failed to review code');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    usage,
    chat,
    analyzeTaskWithAI,
    getInsights,
    generateMeetingNotes,
    reviewCode,
  };
}