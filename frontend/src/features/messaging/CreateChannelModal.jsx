import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Hash, Lock } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import Input from '../../components/ui/Input/Input';
import Button from '../../components/ui/Button/Button';
import styles from './CreateChannelModal.module.css';

const CreateChannelModal = ({ onClose }) => {
  const { currentWorkspace } = useWorkspace();
  const queryClient = useQueryClient();
  
  // Initialize with required 'type' field
  const [formData, setFormData] = useState({ 
    name: '', 
    description: '',
    type: 'public' // Default to public per API requirement
  });

  const mutation = useMutation({
    mutationFn: (data) => {
      // Construct payload strictly matching API docs: name, workspace, type
      const payload = {
        name: data.name,
        description: data.description,
        type: data.type,
        workspace: currentWorkspace?.id
      };
      
      return api.post('/messaging/channels/', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['channels']);
      toast.success(`#${formData.name} created successfully`);
      onClose();
    },
    onError: (error) => {
      console.error(error);
      const msg = error.response?.data?.detail || 'Failed to create channel';
      toast.error(msg);
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!currentWorkspace) {
        toast.error("No workspace selected");
        return;
    }
    if (!formData.name.trim()) {
        toast.error("Channel name is required");
        return;
    }
    mutation.mutate(formData);
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <h3 className={styles.title}>Create Channel</h3>
          <button className={styles.closeBtn} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <p className={styles.description}>
            Channels are where your team communicates. They’re best when organized around a topic.
          </p>

          <Input
            label="Channel Name"
            placeholder="e.g. plan-budget"
            icon={formData.type === 'private' ? Lock : Hash}
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value.toLowerCase().replace(/\s+/g, '-') })}
            required
            autoFocus
          />

          <Input
            label="Description (Optional)"
            placeholder="What's this channel about?"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />

          {/* Channel Type Selection */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 600, color: '#334155' }}>Privacy</label>
            
            <label style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', padding: '0.75rem', border: '1px solid #e2e8f0', borderRadius: '8px', cursor: 'pointer', background: formData.type === 'public' ? '#f8fafc' : 'white' }}>
               <input 
                 type="radio" 
                 name="channelType"
                 checked={formData.type === 'public'}
                 onChange={() => setFormData({ ...formData, type: 'public' })}
                 style={{ accentColor: '#6366f1' }}
               />
               <div style={{ flex: 1 }}>
                 <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, fontSize: '0.9rem', color: '#1e293b' }}>
                    <Hash size={14} /> Public
                 </div>
                 <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Anyone in the workspace can view and join.</div>
               </div>
            </label>

            <label style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', padding: '0.75rem', border: '1px solid #e2e8f0', borderRadius: '8px', cursor: 'pointer', background: formData.type === 'private' ? '#f8fafc' : 'white' }}>
               <input 
                 type="radio" 
                 name="channelType" 
                 checked={formData.type === 'private'}
                 onChange={() => setFormData({ ...formData, type: 'private' })}
                 style={{ accentColor: '#6366f1' }}
               />
               <div style={{ flex: 1 }}>
                 <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, fontSize: '0.9rem', color: '#1e293b' }}>
                    <Lock size={14} /> Private
                 </div>
                 <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Only invited members can view and join.</div>
               </div>
            </label>
          </div>

          <div className={styles.actions}>
            <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
            <Button type="submit" isLoading={mutation.isPending}>Create Channel</Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateChannelModal;