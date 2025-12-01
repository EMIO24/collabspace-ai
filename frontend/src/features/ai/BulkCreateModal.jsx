import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Sparkles, X } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Button from '../../components/ui/Button/Button';
import styles from './BulkCreateModal.module.css';

const BulkCreateModal = ({ projectId, onClose }) => {
  const queryClient = useQueryClient();
  const [prompt, setPrompt] = useState('');

  const mutation = useMutation({
    mutationFn: (text) => api.post('/ai/tasks/auto-create/', { 
      project_id: projectId, 
      prompt: text 
    }),
    onSuccess: (res) => {
      const count = res.data.tasks_created || 'Multiple';
      toast.success(`${count} tasks created successfully!`);
      queryClient.invalidateQueries(['tasks', projectId]);
      onClose();
    },
    onError: () => toast.error('Failed to auto-create tasks.')
  });

  const handleSubmit = () => {
    if (!prompt.trim()) return;
    mutation.mutate(prompt);
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <div className="p-2 bg-purple-100 rounded-lg text-purple-600">
            <Sparkles size={24} />
          </div>
          <div>
            <h2 className={styles.title}>AI Auto-Create</h2>
            <p className="text-sm text-gray-500">Generate tasks from natural language</p>
          </div>
          <button onClick={onClose} className="ml-auto text-gray-400 hover:text-gray-600">
            <X size={24} />
          </button>
        </div>

        <div className={styles.description}>
          Describe your project goals, features, or requirements below. CollabAI will analyze your text and automatically generate a backlog of tasks with appropriate titles and priorities.
        </div>

        <textarea
          className={styles.textarea}
          placeholder="E.g., We need to build a user authentication system with login, registration, password reset, and Google OAuth integration. It should be secure and responsive..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          autoFocus
        />

        <div className={styles.actions}>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            isLoading={mutation.isPending}
            className="bg-gradient-to-r from-indigo-500 to-pink-500 text-white border-none hover:opacity-90"
          >
            <Sparkles size={16} className="mr-2" />
            Generate Tasks
          </Button>
        </div>
      </div>
    </div>
  );
};

export default BulkCreateModal;