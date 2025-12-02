import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Settings, Users, Mail, AlertTriangle, Trash2, Save, Send } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../../services/api';

import Input from '../../../components/ui/Input/Input';
import Button from '../../../components/ui/Button/Button';
import Avatar from '../../../components/ui/Avatar/Avatar';
import Badge from '../../../components/ui/Badge/Badge';
import styles from './WorkspaceSettings.module.css';

const TABS = {
  GENERAL: 'general',
  MEMBERS: 'members',
  INVITES: 'invites'
};

const WorkspaceSettings = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState(TABS.GENERAL);

  // --- TAB 1: GENERAL SETTINGS ---
  const GeneralSettings = () => {
    const { data: workspace } = useQuery({
      queryKey: ['workspace', id],
      queryFn: async () => (await api.get(`/workspaces/${id}/`)).data,
    });

    const [formData, setFormData] = useState({
      name: workspace?.name || '',
      description: workspace?.description || ''
    });

    const [confirmText, setConfirmText] = useState('');

    const updateMutation = useMutation({
      mutationFn: (data) => api.put(`/workspaces/${id}/`, data),
      onSuccess: () => {
        queryClient.invalidateQueries(['workspace', id]);
        toast.success('Workspace updated');
      }
    });

    const deleteMutation = useMutation({
      mutationFn: () => api.delete(`/workspaces/${id}/`),
      onSuccess: () => {
        toast.success('Workspace deleted');
        navigate('/');
      }
    });

    if (!workspace) return <div>Loading...</div>;

    return (
      <div className={styles.contentCard}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.title}>General Settings</h2>
          <p className={styles.subtitle}>Manage your workspace identity.</p>
        </div>

        <form onSubmit={(e) => { e.preventDefault(); updateMutation.mutate(formData); }}>
          <div className={styles.formGroup}>
            <Input 
              label="Workspace Name" 
              value={formData.name}
              onChange={e => setFormData({...formData, name: e.target.value})}
            />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Description</label>
            <textarea
              className={styles.textArea}
              rows={3}
              value={formData.description}
              onChange={e => setFormData({...formData, description: e.target.value})}
            />
          </div>
          <div className={styles.actions}>
            <Button type="submit" isLoading={updateMutation.isPending}>
              <Save size={16} style={{ marginRight: '8px' }} /> Save Changes
            </Button>
          </div>
        </form>

        <div className={styles.dangerZone}>
          <h4 className={styles.dangerTitle}><AlertTriangle size={16} style={{ display: 'inline' }} /> Danger Zone</h4>
          <p className={styles.dangerText}>
            Deleting this workspace will permanently remove all associated projects, tasks, and data.
          </p>
          <input 
            className={styles.confirmInput}
            placeholder="Type 'DELETE' to confirm"
            value={confirmText}
            onChange={e => setConfirmText(e.target.value)}
          />
          <button 
            className={styles.deleteBtn}
            disabled={confirmText !== 'DELETE' || deleteMutation.isPending}
            onClick={() => deleteMutation.mutate()}
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete Workspace'}
          </button>
        </div>
      </div>
    );
  };

  // --- TAB 2: MEMBERS MANAGEMENT ---
  const MemberSettings = () => {
    const { data: members, isLoading } = useQuery({
      queryKey: ['workspaceMembers', id],
      queryFn: async () => (await api.get(`/workspaces/${id}/members/`)).data,
    });

    const removeMutation = useMutation({
      mutationFn: (userId) => api.delete(`/workspaces/${id}/members/${userId}/`),
      onSuccess: () => {
        queryClient.invalidateQueries(['workspaceMembers', id]);
        toast.success('Member removed');
      },
      onError: () => toast.error('Failed to remove member')
    });

    if (isLoading) return <div>Loading members...</div>;

    return (
      <div className={styles.contentCard}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.title}>Team Members</h2>
          <p className={styles.subtitle}>Manage who has access to this workspace.</p>
        </div>

        <table className={styles.table}>
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {members?.map((member) => (
              <tr key={member.id}>
                <td>
                  <div className={styles.userCell}>
                    <Avatar src={member.avatar} fallback={member.username[0]} size="sm" />
                    <div className={styles.userInfo}>
                      <span className={styles.userName}>{member.first_name} {member.last_name}</span>
                      <span className={styles.userEmail}>{member.email}</span>
                    </div>
                  </div>
                </td>
                <td><Badge variant="purple">{member.role || 'Member'}</Badge></td>
                <td><Badge variant="success">Active</Badge></td>
                <td style={{ textAlign: 'right' }}>
                  <button 
                    className={styles.iconBtn}
                    onClick={() => {
                      if(confirm('Remove this member?')) removeMutation.mutate(member.id);
                    }}
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // --- TAB 3: INVITATIONS SYSTEM ---
  const InvitationSettings = () => {
    const [inviteData, setInviteData] = useState({ email: '', role: 'member' });

    const { data: invitations, isLoading } = useQuery({
      queryKey: ['workspaceInvites', id],
      queryFn: async () => (await api.get(`/workspaces/${id}/invitations/`)).data,
    });

    const sendInviteMutation = useMutation({
      mutationFn: (data) => api.post(`/workspaces/${id}/invitations/`, data),
      onSuccess: () => {
        queryClient.invalidateQueries(['workspaceInvites', id]);
        toast.success('Invitation sent');
        setInviteData({ email: '', role: 'member' });
      },
      onError: () => toast.error('Failed to send invite')
    });

    const revokeInviteMutation = useMutation({
      mutationFn: (inviteId) => api.delete(`/workspaces/${id}/invitations/${inviteId}/`),
      onSuccess: () => {
        queryClient.invalidateQueries(['workspaceInvites', id]);
        toast.success('Invitation revoked');
      }
    });

    const handleSend = (e) => {
      e.preventDefault();
      sendInviteMutation.mutate(inviteData);
    };

    return (
      <div className={styles.contentCard}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.title}>Invitations</h2>
          <p className={styles.subtitle}>Invite new users to join your team.</p>
        </div>

        <form onSubmit={handleSend} className={styles.inviteForm}>
          <div style={{ flex: 1 }}>
            <Input 
              placeholder="colleague@company.com" 
              value={inviteData.email}
              onChange={e => setInviteData({...inviteData, email: e.target.value})}
              required
            />
          </div>
          <select 
            className={styles.select}
            value={inviteData.role}
            onChange={e => setInviteData({...inviteData, role: e.target.value})}
          >
            <option value="member">Member</option>
            <option value="admin">Admin</option>
            <option value="viewer">Viewer</option>
          </select>
          <Button type="submit" isLoading={sendInviteMutation.isPending}>
            <Send size={16} style={{ marginRight: '8px' }} /> Send Invite
          </Button>
        </form>

        <h3 className={styles.label}>Pending Invitations</h3>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Email</th>
              <th>Role</th>
              <th>Sent Date</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {invitations?.map((invite) => (
              <tr key={invite.id}>
                <td>{invite.email}</td>
                <td><Badge variant="blue">{invite.role}</Badge></td>
                <td className="text-sm text-gray-500">
                  {new Date(invite.created_at).toLocaleDateString()}
                </td>
                <td style={{ textAlign: 'right' }}>
                  <button 
                    className={styles.iconBtn}
                    onClick={() => revokeInviteMutation.mutate(invite.id)}
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
            {!invitations?.length && (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
                  No pending invitations.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className={styles.container}>
      <div className={styles.sidebar}>
        <button 
          className={`${styles.tabButton} ${activeTab === TABS.GENERAL ? styles.activeTab : ''}`}
          onClick={() => setActiveTab(TABS.GENERAL)}
        >
          <Settings size={18} /> General
        </button>
        <button 
          className={`${styles.tabButton} ${activeTab === TABS.MEMBERS ? styles.activeTab : ''}`}
          onClick={() => setActiveTab(TABS.MEMBERS)}
        >
          <Users size={18} /> Members
        </button>
        <button 
          className={`${styles.tabButton} ${activeTab === TABS.INVITES ? styles.activeTab : ''}`}
          onClick={() => setActiveTab(TABS.INVITES)}
        >
          <Mail size={18} /> Invitations
        </button>
      </div>

      <div className={styles.content}>
        {activeTab === TABS.GENERAL && <GeneralSettings />}
        {activeTab === TABS.MEMBERS && <MemberSettings />}
        {activeTab === TABS.INVITES && <InvitationSettings />}
      </div>
    </div>
  );
};

export default WorkspaceSettings;