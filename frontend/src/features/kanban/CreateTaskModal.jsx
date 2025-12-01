import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Input from '../../components/ui/Input/Input';
import Button from '../../components/ui/Button/Button';
import styles from '../workspaces/CreateWorkspaceModal.module.css'; // Reusing modal styles

const CreateTaskModal = ({ projectId, onClose }) => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    title: '',
    priority: 'medium',
    status: 'todo',
    due_date: ''
  });

  const mutation = useMutation({
    mutationFn: (data) => api.post('/tasks/tasks/', { ...data, project: projectId }),
    onSuccess: () => {
      queryClient.invalidateQueries(['tasks', projectId]);
      toast.success('Task added');
      onClose();
    },
    onError: () => toast.error('Failed to add task')
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <h2 className={styles.title}>Add New Task</h2>
        <form onSubmit={handleSubmit} className={styles.form}>
          <Input
            label="Task Title"
            value={formData.title}
            onChange={e => setFormData({...formData, title: e.target.value})}
            required
            autoFocus
          />
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className={styles.selectWrapper}>
              <label className={styles.label}>Priority</label>
              <select 
                className={styles.input} // Reusing Input styles if possible or custom
                value={formData.priority}
                onChange={e => setFormData({...formData, priority: e.target.value})}
                style={{ border: '1px solid rgba(0,0,0,0.1)', padding: '0.75rem', borderRadius: '8px', width: '100%', background: 'rgba(255,255,255,0.5)' }}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>

            <div className={styles.selectWrapper}>
              <label className={styles.label}>Status</label>
              <select 
                className={styles.input}
                value={formData.status}
                onChange={e => setFormData({...formData, status: e.target.value})}
                style={{ border: '1px solid rgba(0,0,0,0.1)', padding: '0.75rem', borderRadius: '8px', width: '100%', background: 'rgba(255,255,255,0.5)' }}
              >
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="review">Review</option>
                <option value="completed">Completed</option>
              </select>
            </div>
          </div>

          <Input
            label="Due Date"
            type="date"
            value={formData.due_date}
            onChange={e => setFormData({...formData, due_date: e.target.value})}
          />

          <div className={styles.actions}>
            <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
            <Button type="submit" isLoading={mutation.isPending}>Create Task</Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateTaskModal;