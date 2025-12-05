import React, { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../services/api';
import { toast } from 'react-hot-toast';
import { Trash2, Plus } from 'lucide-react';
import Avatar from '../../../components/ui/Avatar/Avatar';
import Button from '../../../components/ui/Button/Button';
import styles from './WorkspaceTabs.module.css';

const WorkspaceMembers = ({ workspaceId }) => {
  const queryClient = useQueryClient();

  // 1. Fetch Raw Data
  const { data: rawData, isLoading } = useQuery({
    queryKey: ['workspaceMembers', workspaceId],
    queryFn: async () => (await api.get(`/workspaces/${workspaceId}/members/`)).data,
  });

  // 2. Normalize Data (Safety Check)
  const members = useMemo(() => {
    if (!rawData) return [];
    if (Array.isArray(rawData)) return rawData;
    if (rawData.results && Array.isArray(rawData.results)) return rawData.results;
    return [];
  }, [rawData]);

  const updateRoleMutation = useMutation({
    mutationFn: ({ userId, role }) => api.put(`/workspaces/${workspaceId}/members/${userId}/`, { role }),
    onSuccess: () => {
      queryClient.invalidateQueries(['workspaceMembers', workspaceId]);
      toast.success('Role updated');
    }
  });

  const removeMutation = useMutation({
    mutationFn: (userId) => api.delete(`/workspaces/${workspaceId}/members/${userId}/`),
    onSuccess: () => {
      queryClient.invalidateQueries(['workspaceMembers', workspaceId]);
      toast.success('Member removed');
    }
  });

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading members...</div>;

  return (
    <div className={styles.glassCard}>
      <div className={styles.toolbar}>
        <h3 className={styles.sectionTitle}>Team Members ({members.length})</h3>
        <Button>
          <Plus size={16} style={{ marginRight: '0.5rem' }} /> Invite Member
        </Button>
      </div>

      <table className={styles.table}>
        <thead>
          <tr>
            <th>User</th>
            <th>Role</th>
            <th>Joined</th>
            <th style={{ textAlign: 'right' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {members.map((member) => (
            <tr key={member.id}>
              <td>
                <div className={styles.userWrapper}>
                  {/* Added safe optional chaining for username access */}
                  <Avatar src={member.avatar} fallback={member.username?.[0] || '?'} />
                  <div>
                    <div className={styles.userName}>{member.first_name} {member.last_name}</div>
                    <div className={styles.userEmail}>{member.email}</div>
                  </div>
                </div>
              </td>
              <td>
                <select 
                  className={styles.roleSelect}
                  value={member.role}
                  onChange={(e) => updateRoleMutation.mutate({ userId: member.id, role: e.target.value })}
                >
                  <option value="owner">Owner</option>
                  <option value="admin">Admin</option>
                  <option value="member">Member</option>
                  <option value="viewer">Viewer</option>
                </select>
              </td>
              <td style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                {new Date(member.date_joined).toLocaleDateString()}
              </td>
              <td style={{ textAlign: 'right' }}>
                <button 
                  className={styles.deleteIconBtn}
                  onClick={() => {
                    if (confirm('Remove this user?')) removeMutation.mutate(member.id);
                  }}
                >
                  <Trash2 size={16} />
                </button>
              </td>
            </tr>
          ))}
          {!members.length && (
            <tr>
              <td colSpan="4" className="p-8 text-center text-gray-500">
                No members found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default WorkspaceMembers;