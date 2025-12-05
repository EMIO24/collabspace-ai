import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../services/api';
import { toast } from 'react-hot-toast';
import { Send, X } from 'lucide-react';
import Button from '../../../components/ui/Button/Button';
import Badge from '../../../components/ui/Badge/Badge';
import styles from './WorkspaceTabs.module.css';

const WorkspaceInvites = ({ workspaceId }) => {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('member');

  const { data: rawData } = useQuery({
    queryKey: ['workspaceInvites', workspaceId],
    queryFn: async () => (await api.get(`/workspaces/${workspaceId}/invitations/`)).data,
  });

  const invites = useMemo(() => {
    if (!rawData) return [];
    if (Array.isArray(rawData)) return rawData;
    if (rawData.results && Array.isArray(rawData.results)) return rawData.results;
    return [];
  }, [rawData]);

  const sendMutation = useMutation({
    mutationFn: (data) => api.post(`/workspaces/${workspaceId}/invitations/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['workspaceInvites', workspaceId]);
      toast.success('Invite sent');
      setEmail('');
    }
  });

  const revokeMutation = useMutation({
    mutationFn: (id) => api.delete(`/workspaces/${workspaceId}/invitations/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries(['workspaceInvites', workspaceId]);
      toast.success('Invite revoked');
    }
  });

  return (
    <div className={styles.inviteGrid}>
      <div className={styles.glassCard} style={{ height: 'fit-content' }}>
        <h3 className={styles.sectionTitle}>Invite New Member</h3>
        <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '1rem' }}>
          Send an email invitation to join this workspace.
        </p>
        
        <form onSubmit={(e) => { e.preventDefault(); sendMutation.mutate({ email, role }); }}>
          <div>
            <label className={styles.formLabel}>Email Address</label>
            <input 
              className={styles.formInput}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              type="email"
            />
          </div>
          <div>
            <label className={styles.formLabel}>Role</label>
            <select 
              className={styles.formSelect}
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option value="admin">Admin</option>
              <option value="member">Member</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
          <Button type="submit" isLoading={sendMutation.isPending} className={styles.fullBtn}>
            <Send size={14} style={{ marginRight: '0.5rem' }} /> Send Invite
          </Button>
        </form>
      </div>

      <div className={styles.glassCard}>
        <h3 className={styles.sectionTitle}>Pending Invitations</h3>
        <table className={styles.table} style={{ marginTop: '1rem' }}>
          <thead>
            <tr>
              <th>Email</th>
              <th>Role</th>
              <th>Sent</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {invites.map((invite) => (
              <tr key={invite.id}>
                <td>{invite.email}</td>
                <td><Badge variant="blue">{invite.role}</Badge></td>
                <td style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                  {new Date(invite.created_at).toLocaleDateString()}
                </td>
                <td style={{ textAlign: 'right' }}>
                  <button 
                    className={styles.deleteIconBtn}
                    onClick={() => revokeMutation.mutate(invite.id)}
                  >
                    <X size={16} />
                  </button>
                </td>
              </tr>
            ))}
            {!invites.length && (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', padding: '2rem', color: '#9ca3af' }}>
                  No pending invitations.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default WorkspaceInvites;