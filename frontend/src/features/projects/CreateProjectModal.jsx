import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import Input from '../../components/ui/Input/Input';
import Button from '../../components/ui/Button/Button';
// Reusing standard modal styles defined previously
import styles from '../workspaces/CreateWorkspaceModal.module.css'; 

const CreateProjectModal = ({ onClose }) => {
  const queryClient = useQueryClient();
  const { currentWorkspace } = useWorkspace();
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    start_date: '',
    end_date: '',
    status: 'active'
  });

  const mutation = useMutation({
    mutationFn: (data) => api.post('/projects/', {
      ...data,
      workspace: currentWorkspace?.id
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['projects']);
      toast.success('Project created successfully');
      onClose();
    },
    onError: () => toast.error('Failed to create project')
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!currentWorkspace) {
      toast.error('No workspace selected');
      return;
    }
    mutation.mutate(formData);
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.title}>Create New Project</h2>
        <form onSubmit={handleSubmit} className={styles.form}>
          <Input 
            label="Project Name"
            placeholder="e.g. Q4 Marketing Campaign"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            required
          />
          
          <Input 
            label="Description"
            placeholder="Briefly describe the goals..."
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
          />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input 
              label="Start Date"
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData({...formData, start_date: e.target.value})}
              required
            />
            <Input 
              label="End Date"
              type="date"
              value={formData.end_date}
              onChange={(e) => setFormData({...formData, end_date: e.target.value})}
              required
            />
          </div>

          <div className={styles.actions}>
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" isLoading={mutation.isPending}>
              Create Project
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateProjectModal;