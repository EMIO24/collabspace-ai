import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Input from '../../components/ui/Input/Input';
import Button from '../../components/ui/Button/Button';
import styles from '../workspaces/CreateWorkspaceModal.module.css'; // Reusing modal styles

const CreateTaskModal = ({ projectId, initialStatus, initialDate, onClose }) => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    title: '',
    priority: 'medium',
    status: initialStatus || 'todo',
    due_date: initialDate || ''
  });

  const mutation = useMutation({
    mutationFn: (data) => {
        // Ensure we have a project ID. If not passed, user might need to select one or backend defaults.
        // For this implementation, we assume a default project or the backend handles it contextually.
        const payload = { ...data };
        if (projectId) payload.project = projectId;
        return api.post('/tasks/tasks/', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['tasks']);
      queryClient.invalidateQueries(['myTasks']);
      queryClient.invalidateQueries(['taskCalendar']);
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
              <label style={{display:'block', fontSize:'0.875rem', fontWeight:600, marginBottom:'0.5rem', color:'#374151'}}>Priority</label>
              <select 
                value={formData.priority}
                onChange={e => setFormData({...formData, priority: e.target.value})}
                style={{ width:'100%', padding:'0.75rem', borderRadius:'8px', border:'1px solid #e5e7eb', background:'white' }}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            <div className={styles.selectWrapper}>
              <label style={{display:'block', fontSize:'0.875rem', fontWeight:600, marginBottom:'0.5rem', color:'#374151'}}>Status</label>
              <select 
                value={formData.status}
                onChange={e => setFormData({...formData, status: e.target.value})}
                style={{ width:'100%', padding:'0.75rem', borderRadius:'8px', border:'1px solid #e5e7eb', background:'white' }}
              >
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="review">Review</option>
                <option value="done">Done</option>
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