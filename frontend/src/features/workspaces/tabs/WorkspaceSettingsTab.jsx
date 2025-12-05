import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../services/api';
import { toast } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import Button from '../../../components/ui/Button/Button';
import styles from './WorkspaceTabs.module.css';

const WorkspaceSettingsTab = ({ workspaceId, initialData }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    name: initialData.name,
    description: initialData.description
  });
  const [deleteConfirm, setDeleteConfirm] = useState('');

  const updateMutation = useMutation({
    mutationFn: (data) => api.put(`/workspaces/${workspaceId}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['workspace', workspaceId]);
      toast.success('Settings saved');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`/workspaces/${workspaceId}/`),
    onSuccess: () => {
      toast.success('Workspace deleted');
      navigate('/workspaces');
    }
  });

  return (
    <div className={styles.settingsContainer}>
      <div className={styles.glassCard}>
        <h3 className={styles.sectionTitle}>General Settings</h3>
        <form onSubmit={(e) => { e.preventDefault(); updateMutation.mutate(formData); }} className={styles.settingsForm}>
          <div>
            <label className={styles.formLabel}>Workspace Name</label>
            <input 
              className={styles.settingsInput}
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
            />
          </div>
          <div>
            <label className={styles.formLabel}>Description</label>
            <textarea 
              className={styles.settingsInput}
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
            />
          </div>
          <div className={styles.actionsRight}>
            <Button type="submit" isLoading={updateMutation.isPending}>Save Changes</Button>
          </div>
        </form>
      </div>

      <div className={styles.dangerZone}>
        <h3 className={styles.dangerTitle}>Delete Workspace</h3>
        <p className={styles.dangerDesc}>
          This action is irreversible. All projects and tasks will be lost.
        </p>
        <div className={styles.dangerActions}>
          <input 
            className={styles.confirmInput}
            placeholder={`Type "${initialData.name}" to confirm`}
            value={deleteConfirm}
            onChange={(e) => setDeleteConfirm(e.target.value)}
          />
          <button 
            className={styles.deleteBtn}
            disabled={deleteConfirm !== initialData.name}
            onClick={() => deleteMutation.mutate()}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};

export default WorkspaceSettingsTab;