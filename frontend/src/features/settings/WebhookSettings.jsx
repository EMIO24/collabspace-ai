import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Webhook, Plus, Trash2, Activity } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Button from '../../components/ui/Button/Button';
import Input from '../../components/ui/Input/Input';
import styles from './WebhookSettings.module.css';

const WebhookSettings = () => {
  const queryClient = useQueryClient();
  const [newUrl, setNewUrl] = useState('');

  const { data: webhooks, isLoading } = useQuery({
    queryKey: ['webhooks'],
    queryFn: async () => (await api.get('/integrations/webhooks/')).data,
  });

  const createMutation = useMutation({
    mutationFn: (url) => api.post('/integrations/webhooks/', { 
      target_url: url, 
      events: ['task.created', 'task.completed'] 
    }),
    onSuccess: () => {
      toast.success('Webhook added');
      setNewUrl('');
      queryClient.invalidateQueries(['webhooks']);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/integrations/webhooks/${id}/`),
    onSuccess: () => {
      toast.success('Webhook removed');
      queryClient.invalidateQueries(['webhooks']);
    }
  });

  return (
    <div>
      <div className={styles.pageHeader}>
        <h2 className={styles.title}>Webhooks</h2>
        <p className={styles.subtitle}>Send real-time data to external services.</p>
      </div>

      <div className={styles.section}>
        <div className={styles.inputGroup}>
          <div className={styles.inputWrapper}>
            <Input 
              placeholder="https://api.your-service.com/webhook" 
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
            />
          </div>
          <Button onClick={() => createMutation.mutate(newUrl)} isLoading={createMutation.isPending}>
            <Plus size={16} style={{ marginRight: '8px' }} /> Add Webhook
          </Button>
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionHeader}>Active Endpoints</h3>
        <div>
          {isLoading ? (
            <div>Loading...</div>
          ) : webhooks?.map((hook) => (
            <div key={hook.id} className={styles.webhookItem}>
              <div className={styles.hookInfo}>
                <div className={styles.iconBox}>
                  <Webhook size={18} />
                </div>
                <div>
                  <div className={styles.url}>{hook.target_url}</div>
                  <div className={styles.meta}>
                    <Activity size={12} /> Active • {hook.events?.length || 0} events subscribed
                  </div>
                </div>
              </div>
              <button 
                onClick={() => deleteMutation.mutate(hook.id)}
                className={styles.deleteBtn}
                title="Remove Webhook"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
          
          {!webhooks?.length && !isLoading && (
            <div className={styles.emptyState}>
              No webhooks configured.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WebhookSettings;