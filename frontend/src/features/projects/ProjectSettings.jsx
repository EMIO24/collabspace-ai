import React, { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Settings, Users, AlertTriangle, Save, Tag, Plus, X, Trash2 } from 'lucide-react';
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
  LABELS: 'labels',
  DANGER: 'danger'
};

const ProjectSettings = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState(TABS.GENERAL);

  // --- TAB 1: GENERAL ---
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
          <div className={styles.formGroup}>
            <label className={styles.label}>Description</label>
            <textarea
              className={styles.textArea}
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
          <div className={styles.actions}>
            <Button type="submit" isLoading={mutation.isPending}>
              <Save size={18} style={{ marginRight: '0.5rem' }} /> Save Changes
            </Button>
          </div>
        </form>
      </div>
    );
  };

  // --- TAB 2: MEMBERS ---
  const MembersSettings = () => {
    const [emailToAdd, setEmailToAdd] = useState('');
    
    const { data: rawMembers } = useQuery({
      queryKey: ['projectMembers', id],
      queryFn: async () => (await api.get(`/projects/${id}/members/`)).data
    });

    // FIX: Data Normalization
    const members = useMemo(() => {
      if (!rawMembers) return [];
      if (Array.isArray(rawMembers)) return rawMembers;
      return rawMembers.results || [];
    }, [rawMembers]);

    const addMemberMutation = useMutation({
      mutationFn: (email) => api.post(`/projects/${id}/members/`, { email }),
      onSuccess: () => {
        queryClient.invalidateQueries(['projectMembers', id]);
        toast.success('Member invited');
        setEmailToAdd('');
      },
      onError: () => toast.error('Failed to invite member')
    });

    const removeMemberMutation = useMutation({
      mutationFn: (userId) => api.delete(`/projects/${id}/members/${userId}/`),
      onSuccess: () => {
        queryClient.invalidateQueries(['projectMembers', id]);
        toast.success('Member removed');
      }
    });

    return (
        <div className={styles.contentCard}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 className={styles.sectionTitle} style={{margin:0, border:'none'}}>Team Members</h2>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <input 
                        className={styles.confirmInput} 
                        style={{ marginBottom: 0, minWidth: '200px' }}
                        placeholder="Enter email..."
                        value={emailToAdd}
                        onChange={(e) => setEmailToAdd(e.target.value)}
                    />
                    <Button size="sm" onClick={() => addMemberMutation.mutate(emailToAdd)} disabled={!emailToAdd}>
                        <Plus size={16} /> Add
                    </Button>
                </div>
            </div>

            <div style={{ overflowX: 'auto' }}>
                <table className={styles.table}>
                    <thead>
                        <tr>
                            <th>USER</th>
                            <th>ROLE</th>
                            <th style={{ textAlign: 'right' }}>ACTIONS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {members.map(member => (
                            <tr key={member.id}>
                                <td>
                                    <div className={styles.userCell}>
                                        <Avatar src={member.avatar} fallback={member.username?.[0] || 'U'} size="sm" />
                                        <div>
                                            <div className={styles.userName}>
                                                {member.first_name ? `${member.first_name} ${member.last_name}` : member.username}
                                            </div>
                                            <div className={styles.userEmail}>{member.email}</div>
                                        </div>
                                    </div>
                                </td>
                                <td><Badge variant="blue">{member.role || 'Member'}</Badge></td>
                                <td style={{ textAlign: 'right' }}>
                                    <button 
                                        className={styles.iconBtn}
                                        onClick={() => { if(confirm('Remove user?')) removeMemberMutation.mutate(member.id) }}
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {!members.length && <tr><td colSpan="3" style={{padding:'2rem', textAlign:'center', color:'#9ca3af'}}>No members yet.</td></tr>}
                    </tbody>
                </table>
            </div>
        </div>
    );
  };

  // --- TAB 3: LABELS ---
  const LabelsSettings = () => {
    const [newLabel, setNewLabel] = useState('');
    
    const { data: rawLabels } = useQuery({
      queryKey: ['projectLabels', id],
      queryFn: async () => (await api.get(`/projects/${id}/labels/`)).data
    });

    // FIX: Data Normalization
    const labels = useMemo(() => {
      if (!rawLabels) return [];
      if (Array.isArray(rawLabels)) return rawLabels;
      return rawLabels.results || [];
    }, [rawLabels]);

    const createLabel = useMutation({
      mutationFn: (name) => api.post(`/projects/${id}/labels/`, { name, color: '#3b82f6' }),
      onSuccess: () => {
        queryClient.invalidateQueries(['projectLabels', id]);
        setNewLabel('');
        toast.success('Label created');
      }
    });

    const deleteLabel = useMutation({
      mutationFn: (labelId) => api.delete(`/projects/${id}/labels/${labelId}/`),
      onSuccess: () => {
        queryClient.invalidateQueries(['projectLabels', id]);
        toast.success('Label deleted');
      }
    });

    return (
      <div className={styles.contentCard}>
         <h2 className={styles.sectionTitle}>Project Labels</h2>
         <p className={styles.sectionDesc}>Categorize tasks with custom colored tags.</p>

         <div className={styles.addLabelRow}>
            <div style={{ flex: 1 }}>
              <Input 
                 placeholder="New Label Name" 
                 value={newLabel}
                 onChange={(e) => setNewLabel(e.target.value)}
              />
            </div>
            <Button onClick={() => createLabel.mutate(newLabel)} disabled={!newLabel.trim()}>
               <Plus size={16} style={{ marginRight: '4px' }} /> Add
            </Button>
         </div>

         <div className={styles.labelsContainer}>
            {labels.map(label => (
               <div key={label.id} className={styles.labelChip}>
                  <div className={styles.labelColor} style={{ background: label.color }} />
                  <span className={styles.labelName}>{label.name}</span>
                  <button onClick={() => deleteLabel.mutate(label.id)} className={styles.deleteLabelBtn}>
                     <X size={14} />
                  </button>
               </div>
            ))}
            {!labels.length && <p className={styles.emptyState}>No labels created yet.</p>}
         </div>
      </div>
    );
  };

  // --- TAB 4: DANGER ZONE ---
  const DangerSettings = () => {
    const [confirmText, setConfirmText] = useState('');
    const [projectData] = useState(queryClient.getQueryData(['project', id]));

    const archiveMutation = useMutation({
        mutationFn: () => api.put(`/projects/${id}/`, { status: 'archived' }),
        onSuccess: () => {
            toast.success("Project archived");
            navigate('/projects');
        }
    });

    const deleteMutation = useMutation({
        mutationFn: () => api.delete(`/projects/${id}/`),
        onSuccess: () => {
            toast.success("Project deleted");
            navigate('/projects');
        }
    });

    return (
        <div className={styles.contentCard} style={{ borderColor: '#fca5a5' }}>
            <h2 className={styles.sectionTitle} style={{ color: '#ef4444' }}>Danger Zone</h2>
            
            <div className={styles.dangerBox}>
                <h4 className={styles.dangerTitle}>Archive Project</h4>
                <p className={styles.dangerDesc}>Mark this project as archived. Read-only mode for all members.</p>
                <Button variant="ghost" onClick={() => archiveMutation.mutate()}>Archive Project</Button>
            </div>

            <div className={styles.dangerBox} style={{ background: '#fef2f2', borderColor: '#fecaca' }}>
                <h4 className={styles.dangerTitle}>Delete Project</h4>
                <p className={styles.dangerDesc}>Irreversible action. Please type <strong>{projectData?.name}</strong> to confirm.</p>
                
                <input 
                    className={styles.confirmInput}
                    placeholder={`Type "${projectData?.name}"`}
                    value={confirmText}
                    onChange={(e) => setConfirmText(e.target.value)}
                />
                <button 
                    className={styles.deleteBtn}
                    disabled={confirmText !== projectData?.name}
                    onClick={() => deleteMutation.mutate()}
                >
                    Delete Permanently
                </button>
            </div>
        </div>
    );
  };

  return (
    <div className={styles.container}>
      <div className={styles.sidebar}>
        <button className={`${styles.tabButton} ${activeTab === TABS.GENERAL ? styles.activeTab : ''}`} onClick={() => setActiveTab(TABS.GENERAL)}>
          <Settings size={18} /> General
        </button>
        <button className={`${styles.tabButton} ${activeTab === TABS.MEMBERS ? styles.activeTab : ''}`} onClick={() => setActiveTab(TABS.MEMBERS)}>
          <Users size={18} /> Members
        </button>
        <button className={`${styles.tabButton} ${activeTab === TABS.LABELS ? styles.activeTab : ''}`} onClick={() => setActiveTab(TABS.LABELS)}>
          <Tag size={18} /> Labels
        </button>
        <button className={`${styles.tabButton} ${activeTab === TABS.DANGER ? styles.activeTab : ''} ${styles.dangerTab}`} onClick={() => setActiveTab(TABS.DANGER)}>
          <AlertTriangle size={18} /> Danger Zone
        </button>
      </div>

      <div className={styles.content}>
        {activeTab === TABS.GENERAL && <GeneralSettings />}
        {activeTab === TABS.MEMBERS && <MembersSettings />}
        {activeTab === TABS.LABELS && <LabelsSettings />}
        {activeTab === TABS.DANGER && <DangerSettings />}
      </div>
    </div>
  );
};

export default ProjectSettings;