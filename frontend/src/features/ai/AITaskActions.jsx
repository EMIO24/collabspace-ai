import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Sparkles, ListTree, Clock, FileText } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import styles from './AITaskActions.module.css';

const AITaskActions = ({ taskId }) => {
  const queryClient = useQueryClient();
  const [aiResponse, setAiResponse] = useState(null);

  // Generic mutation handler for AI actions
  const useAIMutation = (endpoint, successMsg) => {
    return useMutation({
      mutationFn: () => api.post(endpoint, { task_id: taskId }),
      onSuccess: (res) => {
        toast.success(successMsg);
        // If the backend returns a direct text result (like summary), show it
        if (res.data.result) {
          setAiResponse(res.data.result);
        }
        // Always refresh task data as AI might have updated fields (e.g. estimate)
        queryClient.invalidateQueries(['task', taskId]);
      },
      onError: () => toast.error('AI Magic failed. Try again.')
    });
  };

  const summarizeMutation = useAIMutation('/ai/tasks/summarize/', 'Task summarized!');
  const breakdownMutation = useAIMutation('/ai/tasks/breakdown/', 'Subtasks created!');
  const estimateMutation = useAIMutation('/ai/tasks/estimate/', 'Time estimation updated!');

  const isLoading = summarizeMutation.isPending || breakdownMutation.isPending || estimateMutation.isPending;

  return (
    <div className={styles.container}>
      <div className={styles.label}>
        <Sparkles size={14} className="text-purple-500" />
        AI Actions
      </div>
      
      <button 
        className={styles.magicBtn}
        onClick={() => summarizeMutation.mutate()}
        disabled={isLoading}
      >
        <FileText size={16} className={styles.icon} />
        Summarize
      </button>

      <button 
        className={styles.magicBtn}
        onClick={() => breakdownMutation.mutate()}
        disabled={isLoading}
      >
        <ListTree size={16} className={styles.icon} />
        Breakdown
      </button>

      <button 
        className={styles.magicBtn}
        onClick={() => estimateMutation.mutate()}
        disabled={isLoading}
      >
        <Clock size={16} className={styles.icon} />
        Estimate Time
      </button>

      {aiResponse && (
        <div className={styles.responseBox}>
          <strong>AI Insight:</strong>
          <p>{aiResponse}</p>
          <button 
            className="text-xs text-gray-500 mt-2 underline"
            onClick={() => setAiResponse(null)}
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};

export default AITaskActions;