import React, { useState } from 'react';
import { useAI } from '../../hooks/useAI';
import { generateTaskAnalysisPrompt, generateTaskBreakdown } from '../../utils/aiPrompts';
import AILoadingState from './AILoadingState';
import styles from './TaskAIActions.module.css';

function TaskAIActions({ task, onUpdate }) {
  const { loading, analyzeTaskWithAI, chat } = useAI();
  const [showResults, setShowResults] = useState(false);
  const [results, setResults] = useState(null);
  const [activeAction, setActiveAction] = useState(null);

  const handleAnalyze = async () => {
    setActiveAction('analyze');
    setShowResults(true);

    try {
      const prompt = generateTaskAnalysisPrompt(task);
      const response = await chat([
        { role: 'system', content: 'You are a task analysis expert.' },
        { role: 'user', content: prompt },
      ]);
      setResults({ type: 'analysis', content: response.content });
    } catch (error) {
      setResults({ type: 'error', content: 'Failed to analyze task' });
    } finally {
      setActiveAction(null);
    }
  };

  const handleBreakdown = async () => {
    setActiveAction('breakdown');
    setShowResults(true);

    try {
      const prompt = generateTaskBreakdown(task);
      const response = await chat([
        { role: 'system', content: 'You are a task breakdown expert.' },
        { role: 'user', content: prompt },
      ]);
      setResults({ type: 'breakdown', content: response.content });
    } catch (error) {
      setResults({ type: 'error', content: 'Failed to break down task' });
    } finally {
      setActiveAction(null);
    }
  };

  const handleEstimate = async () => {
    setActiveAction('estimate');
    setShowResults(true);

    try {
      const prompt = `Estimate the time required to complete this task:
      
Title: ${task.title}
Description: ${task.description || 'No description'}
Complexity: ${task.complexity || 'Unknown'}

Provide:
1. Estimated hours
2. Confidence level
3. Factors affecting the estimate`;

      const response = await chat([
        { role: 'system', content: 'You are a time estimation expert.' },
        { role: 'user', content: prompt },
      ]);
      setResults({ type: 'estimate', content: response.content });
    } catch (error) {
      setResults({ type: 'error', content: 'Failed to estimate time' });
    } finally {
      setActiveAction(null);
    }
  };

  const handleSuggestPriority = async () => {
    setActiveAction('priority');
    setShowResults(true);

    try {
      const prompt = `Suggest a priority level for this task:
      
Title: ${task.title}
Description: ${task.description || 'No description'}
Due Date: ${task.dueDate || 'Not set'}
Current Priority: ${task.priority || 'Not set'}

Explain your reasoning.`;

      const response = await chat([
        { role: 'system', content: 'You are a prioritization expert.' },
        { role: 'user', content: prompt },
      ]);
      setResults({ type: 'priority', content: response.content });
    } catch (error) {
      setResults({ type: 'error', content: 'Failed to suggest priority' });
    } finally {
      setActiveAction(null);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.actions}>
        <button
          className={styles.actionButton}
          onClick={handleAnalyze}
          disabled={loading}
        >
          <span className={styles.buttonIcon}>🔍</span>
          Analyze Task
        </button>

        <button
          className={styles.actionButton}
          onClick={handleBreakdown}
          disabled={loading}
        >
          <span className={styles.buttonIcon}>📋</span>
          Break Down
        </button>

        <button
          className={styles.actionButton}
          onClick={handleEstimate}
          disabled={loading}
        >
          <span className={styles.buttonIcon}>⏱️</span>
          Estimate Time
        </button>

        <button
          className={styles.actionButton}
          onClick={handleSuggestPriority}
          disabled={loading}
        >
          <span className={styles.buttonIcon}>🎯</span>
          Suggest Priority
        </button>
      </div>

      {loading && activeAction && (
        <AILoadingState message={`Analyzing your task...`} />
      )}

      {showResults && results && !loading && (
        <div className={styles.results}>
          <div className={styles.resultsHeader}>
            <h4 className={styles.resultsTitle}>
              {results.type === 'analysis' && '🔍 Task Analysis'}
              {results.type === 'breakdown' && '📋 Task Breakdown'}
              {results.type === 'estimate' && '⏱️ Time Estimate'}
              {results.type === 'priority' && '🎯 Priority Suggestion'}
              {results.type === 'error' && '⚠️ Error'}
            </h4>
            <button
              className={styles.closeButton}
              onClick={() => setShowResults(false)}
            >
              ×
            </button>
          </div>
          <div className={styles.resultsContent}>
            {results.content}
          </div>
        </div>
      )}
    </div>
  );
}

export default TaskAIActions;