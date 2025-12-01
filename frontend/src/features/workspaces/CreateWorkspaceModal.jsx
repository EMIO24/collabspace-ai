import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import { toast } from 'react-hot-toast';
import Input from '../../components/ui/Input/Input';
import Button from '../../components/ui/Button/Button';
import styles from './CreateWorkspaceModal.module.css';

const CreateWorkspaceModal = ({ onClose, initialData = null }) => {
  const queryClient = useQueryClient();
  const { setCurrentWorkspace, refetchWorkspaces } = useWorkspace();
  const isEditMode = !!initialData;
  
  const [formData, setFormData] = useState({
    name: initialData?.name || '',
    slug: initialData?.slug || '',
    description: initialData?.description || ''
  });

  // Create Mutation
  const createMutation = useMutation({
    mutationFn: (data) => api.post('/workspaces/', data),
    onSuccess: (res) => {
      refetchWorkspaces();
      setCurrentWorkspace(res.data);
      toast.success('Workspace created!');
      onClose();
    },
    onError: () => toast.error('Failed to create workspace.')
  });

  // Edit Mutation
  const editMutation = useMutation({
    mutationFn: (data) => api.put(`/workspaces/${initialData?.id}/`, data),
    onSuccess: (res) => {
      refetchWorkspaces();
      // Only update current context if we edited the active one
      if (initialData.id === res.data.id) {
        setCurrentWorkspace(res.data);
      }
      toast.success('Workspace updated!');
      onClose();
    },
    onError: () => toast.error('Failed to update workspace.')
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isEditMode) {
      editMutation.mutate(formData);
    } else {
      createMutation.mutate(formData);
    }
  };

  const isLoading = createMutation.isPending || editMutation.isPending;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <h2 className={styles.title}>
          {isEditMode ? 'Edit Workspace' : 'Create New Workspace'}
        </h2>
        
        <form onSubmit={handleSubmit} className={styles.form}>
          <Input 
            label="Workspace Name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            placeholder="Acme Corp"
            required
          />
          
          <Input 
            label="URL Slug"
            value={formData.slug}
            onChange={(e) => setFormData({...formData, slug: e.target.value})}
            placeholder="acme-corp"
            required
          />

          <Input 
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
            placeholder="What is this team for?"
          />

          <div className={styles.actions}>
            <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
            <Button type="submit" isLoading={isLoading}>
              {isEditMode ? 'Save Changes' : 'Create Workspace'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateWorkspaceModal;