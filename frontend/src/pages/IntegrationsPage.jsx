import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { api } from '../services/api';
import IntegrationCard from '../features/integrations/IntegrationCard';
import Input from '../components/ui/Input/Input';
import Button from '../components/ui/Button/Button';
import styles from '../features/integrations/Integrations.module.css';

const IntegrationsPage = () => {
  const queryClient = useQueryClient();
  const [selectedIntegration, setSelectedIntegration] = useState(null);
  const [token, setToken] = useState('');

  // 1. Fetch Integrations
  const { data: integrations, isLoading } = useQuery({
    queryKey: ['integrations'],
    queryFn: async () => {
      const res = await api.get('/integrations/integrations/');
      return res.data; 
      // Expected: [{ id: 1, provider: 'github', name: 'GitHub', status: 'disconnected', ... }]
    }
  });

  // 2. Connect Mutation (Token Flow)
  const connectMutation = useMutation({
    mutationFn: (data) => api.post('/integrations/integrations/', data),
    onSuccess: () => {
      toast.success(`Connected to ${selectedIntegration.name}`);
      queryClient.invalidateQueries(['integrations']);
      closeModal();
    },
    onError: () => toast.error('Connection failed. Check your token.')
  });

  const handleConnectClick = (integration) => {
    // If it's a simple token flow (like prompt requested for GitHub via POST)
    setSelectedIntegration(integration);
  };

  const handleConfirmConnect = (e) => {
    e.preventDefault();
    if (!token) return;

    connectMutation.mutate({
      provider: selectedIntegration.provider,
      config: { token }
    });
  };

  const closeModal = () => {
    setSelectedIntegration(null);
    setToken('');
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Integrations</h1>
        <p className={styles.subtitle}>Supercharge your workspace with external tools.</p>
      </div>

      <div className={styles.grid}>
        {isLoading ? (
          <div>Loading marketplace...</div>
        ) : integrations?.map((integration) => (
          <IntegrationCard 
            key={integration.id} 
            integration={integration} 
            onConnect={handleConnectClick}
          />
        ))}
      </div>

      {/* Connect Modal (Token Input) */}
      {selectedIntegration && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <h2 className={styles.name}>Connect {selectedIntegration.name}</h2>
            <p className={styles.description} style={{ marginBottom: '1.5rem' }}>
              Enter your Personal Access Token (PAT) to authorize this integration.
            </p>
            
            <form onSubmit={handleConfirmConnect}>
              <Input
                label="Access Token"
                type="password"
                placeholder="ghp_..."
                value={token}
                onChange={(e) => setToken(e.target.value)}
                required
              />
              
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
                <Button variant="ghost" type="button" onClick={closeModal}>Cancel</Button>
                <Button type="submit" isLoading={connectMutation.isPending}>
                  Connect
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default IntegrationsPage;