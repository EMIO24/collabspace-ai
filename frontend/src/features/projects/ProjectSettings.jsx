import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Settings, Users, AlertTriangle, Save, Trash2, Plus 
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';

import Input from '../../components/ui/Input/Input';
import Button from '../../components/ui/Button/Button';
import Avatar from '../../components/ui/Avatar/Avatar';
import Badge from '../../components/ui/Badge/Badge';
import styles from './ProjectSettings.module.css';

const TABS = {
  GENERAL: 'general',
  MEMBERS: 'members',
  DANGER: 'danger'
};

const ProjectSettings = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState(TABS.GENERAL);

  // --- TAB 1: GENERAL SETTINGS ---
  const GeneralSettings = () => {
    const { data: project } = useQuery({
      queryKey: ['project', id],
      queryFn: async () => (await api.get(`/projects/${id}/`)).data,
    });

    const [formData, setFormData] = useState({
      name: project?.name || '',
      slug: project?.slug || '',
      description: project?.description || '',
      start_date: project?.start_date || '',
      end_date: project?.end_date || ''
    });

    const mutation = useMutation({
      mutationFn: (data) => api.put(`/projects/${id}/`, data),
      onSuccess: () => {
        queryClient.invalidateQueries(['project', id]);
        toast.success('Project updated successfully');
      },
      onError: () => toast.error('Failed to update project')
    });

    if (!project) return <div>Loading...</div>;

    return (
      <div className={styles.contentCard}>
        <h2 className={styles.sectionTitle}>General Settings</h2>
        <form 
          className={styles.form}
          onSubmit={(e) => { e.preventDefault(); mutation.mutate(formData); }}
        >
          <Input 
            label="Project Name" 
            value={formData.name}
            onChange={e => setFormData({...formData, name: e.target.value})}
          />
          <Input 
            label="URL Slug" 
            value={formData.slug}
            onChange={e => setFormData({...formData, slug: e.target.value})}
          />
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-gray-700 ml-1">Description</label>
            <textarea
              className="w-full p-3 rounded-lg border border-gray-200 bg-white/50 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
              rows={4}
              value={formData.description}
              onChange={e => setFormData({...formData, description: e.target.value})}
            />
          </div>
          <div className={styles.row}>
            <Input 
              type="date" 
              label="Start Date" 
              value={formData.start_date}
              onChange={e => setFormData({...formData, start_date: e.target.value})}
            />
            <Input 
              type="date" 
              label="End Date" 
              value={formData.end_date}
              onChange={e => setFormData({...formData, end_date: e.target.value})}
            />
          </div>
          <div className="flex justify-end pt-4">
            <Button type="submit" isLoading={mutation.isPending}>
              <Save size={18} className="mr-2" /> Save Changes
            </Button>
          </div>
        </form>
      </div>
    );
  };

  // --- TAB 2: MEMBERS MANAGEMENT ---
  const MembersSettings = () => {
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [emailToAdd, setEmailToAdd] = useState('');

    const { data: members } = useQuery({
      queryKey: ['projectMembers', id],
      queryFn: async () => (await api.get(`/projects/${id}/members/`)).data,
    });

    const addMutation = useMutation({
      mutationFn: (email) => api.post(`/projects/${id}/members/`, { email, role: 'member' }),
      onSuccess: () => {
        queryClient.invalidateQueries(['projectMembers', id]);
        toast.success('Member added');
        setIsAddModalOpen(false);
        setEmailToAdd('');
      },
      onError: () => toast.error('Failed to add member')
    });

    const removeMutation = useMutation({
      mutationFn: (userId) => api.delete(`/projects/${id}/members/${userId}/`),
      onSuccess: () => {
        queryClient.invalidateQueries(['projectMembers', id]);
        toast.success('Member removed');
      }
    });

    return (
      <div className={styles.contentCard}>
        <div className={styles.memberHeader}>
          <h2 className={styles.sectionTitle} style={{ margin: 0, border: 'none' }}>Team Members</h2>
          <Button size="sm" onClick={() => setIsAddModalOpen(true)}>
            <Plus size={16} className="mr-2" /> Add Member
          </Button>
        </div>

        <div className={styles.tableContainer}>
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
              {members?.map(member => (
                <tr key={member.id}>
                  <td>
                    <div className={styles.userCell}>
                      <Avatar src={member.avatar} fallback={member.username[0]} />
                      <div>
                        <div className={styles.userName}>{member.first_name} {member.last_name}</div>
                        <div className={styles.userEmail}>{member.email}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <Badge variant="purple">{member.role || 'Member'}</Badge>
                  </td>
                  <td className="text-sm text-gray-500">
                    {new Date(member.date_joined).toLocaleDateString()}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button 
                      className={styles.actionBtn}
                      onClick={() => {
                        if (confirm('Remove this user?')) removeMutation.mutate(member.id);
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

        {isAddModalOpen && (
          <div className={styles.overlay} onClick={() => setIsAddModalOpen(false)}>
            <div className={styles.modal} onClick={e => e.stopPropagation()}>
              <h3 className="text-lg font-bold mb-4">Add Team Member</h3>
              <Input 
                label="User Email"
                placeholder="colleague@company.com"
                value={emailToAdd}
                onChange={e => setEmailToAdd(e.target.value)}
                autoFocus
              />
              <div className="flex justify-end gap-2 mt-6">
                <Button variant="ghost" onClick={() => setIsAddModalOpen(false)}>Cancel</Button>
                <Button onClick={() => addMutation.mutate(emailToAdd)} isLoading={addMutation.isPending}>
                  Send Invite
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // --- TAB 3: DANGER ZONE ---
  const DangerSettings = () => {
    const [confirmText, setConfirmText] = useState('');
    
    // UPDATED: Archive now uses PUT update instead of custom endpoint
    const archiveMutation = useMutation({
      mutationFn: () => api.put(`/projects/${id}/`, { status: 'archived' }),
      onSuccess: () => {
        toast.success('Project archived');
        navigate('/dashboard');
      },
      onError: () => toast.error('Failed to archive project')
    });

    const deleteMutation = useMutation({
      mutationFn: () => api.delete(`/projects/${id}/`),
      onSuccess: () => {
        toast.success('Project deleted');
        navigate('/dashboard');
      }
    });

    return (
      <div className={styles.contentCard} style={{ borderColor: 'var(--danger-light)' }}>
        <h2 className={styles.sectionTitle} style={{ color: 'var(--danger)' }}>Danger Zone</h2>
        
        <div className={styles.dangerBox}>
          <h4 className={styles.dangerTitle}>Archive Project</h4>
          <p className={styles.dangerDesc}>
            Archiving removes this project from the active list but keeps data intact.
          </p>
          <Button 
            variant="ghost" 
            className="border border-gray-300"
            onClick={() => {
              if(confirm('Archive this project?')) archiveMutation.mutate();
            }}
            isLoading={archiveMutation.isPending}
          >
            Archive Project
          </Button>
        </div>

        <div className={styles.dangerBox} style={{ background: 'rgba(254, 226, 226, 0.4)' }}>
          <h4 className={styles.dangerTitle}>Delete Project</h4>
          <p className={styles.dangerDesc}>
            Permanently remove this project and all associated tasks. This action cannot be undone.
          </p>
          
          <input 
            className={styles.confirmInput}
            placeholder="Type 'DELETE' to confirm"
            value={confirmText}
            onChange={e => setConfirmText(e.target.value)}
          />
          
          <Button 
            className="bg-red-600 hover:bg-red-700 text-white border-none w-full"
            disabled={confirmText !== 'DELETE' || deleteMutation.isPending}
            onClick={() => deleteMutation.mutate()}
          >
            Delete this project
          </Button>
        </div>
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
          className={`${styles.tabButton} ${activeTab === TABS.DANGER ? styles.activeTab : ''} ${styles.dangerTab}`}
          onClick={() => setActiveTab(TABS.DANGER)}
        >
          <AlertTriangle size={18} /> Danger Zone
        </button>
      </div>

      <div className={styles.content}>
        {activeTab === TABS.GENERAL && <GeneralSettings />}
        {activeTab === TABS.MEMBERS && <MembersSettings />}
        {activeTab === TABS.DANGER && <DangerSettings />}
      </div>
    </div>
  );
};

export default ProjectSettings;