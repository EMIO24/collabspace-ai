import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import { toast } from 'react-hot-toast';
import Input from '../../components/ui/Input/Input';
import Button from '../../components/ui/Button/Button';
import styles from './CreateWorkspaceModal.module.css';

const CreateWorkspaceModal = ({ onClose }) => {
  const queryClient = useQueryClient();
  const { setCurrentWorkspace, refetchWorkspaces } = useWorkspace();
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    // Hidden setting field as per requirements
    settings: {
      theme: 'light'
    }
  });

  const createMutation = useMutation({
    mutationFn: (data) => api.post('/workspaces/', data),
    onSuccess: (res) => {
      refetchWorkspaces();
      setCurrentWorkspace(res.data);
      toast.success('Workspace created successfully!');
      onClose();
    },
    onError: () => toast.error('Failed to create workspace.')
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <h2 className={styles.title}>Create Workspace</h2>
          <p className={styles.subtitle}>Set up a new shared environment for your team.</p>
        </div>
        
        <form onSubmit={handleSubmit} className={styles.form}>
          <Input 
            label="Workspace Name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            placeholder="e.g. Engineering Team"
            required
            autoFocus
          />

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Description</label>
            <textarea 
              className={styles.textArea}
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="What is this workspace for?"
            />
          </div>

          <div className={styles.actions}>
            <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
            <Button type="submit" isLoading={createMutation.isPending}>
              Create Workspace
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateWorkspaceModal;