import React, { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import { Calendar, Tag, Plus, X, Layers, CheckCircle2, Clock } from 'lucide-react';
import BurndownChart from '../analytics/BurndownChart';
import styles from './ProjectOverview.module.css';
import Badge from '../../components/ui/Badge/Badge';
import Avatar from '../../components/ui/Avatar/Avatar';

const ProjectOverview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isAddingLabel, setIsAddingLabel] = useState(false);
  const [newLabelName, setNewLabelName] = useState('');
  
  const { data: project } = useQuery({
    queryKey: ['project', id],
    queryFn: async () => (await api.get(`/projects/${id}/`)).data
  });

  const { data: rawLabels } = useQuery({
    queryKey: ['projectLabels', id],
    queryFn: async () => (await api.get(`/projects/${id}/labels/`)).data || []
  });

  const labels = useMemo(() => {
    if (!rawLabels) return [];
    if (Array.isArray(rawLabels)) return rawLabels;
    return rawLabels.results || [];
  }, [rawLabels]);

  const { data: rawMembers } = useQuery({
    queryKey: ['projectMembers', id],
    queryFn: async () => (await api.get(`/projects/${id}/members/`)).data
  });

  const members = useMemo(() => {
    if (!rawMembers) return [];
    if (Array.isArray(rawMembers)) return rawMembers;
    return rawMembers.results || [];
  }, [rawMembers]);

  // ... (Mutations remain the same)
  const updateMutation = useMutation({
    mutationFn: (data) => api.put(`/projects/${id}/`, data),
    onSuccess: () => queryClient.invalidateQueries(['project', id])
  });

  const createLabelMutation = useMutation({
    mutationFn: (name) => api.post(`/projects/${id}/labels/`, { name, color: '#3b82f6' }),
    onSuccess: () => {
      queryClient.invalidateQueries(['projectLabels', id]);
      setNewLabelName('');
      setIsAddingLabel(false);
    }
  });

  const deleteLabelMutation = useMutation({
    mutationFn: (labelId) => api.delete(`/projects/${id}/labels/${labelId}/`),
    onSuccess: () => queryClient.invalidateQueries(['projectLabels', id])
  });

  const handleDateChange = (field, value) => {
    updateMutation.mutate({ [field]: value });
  };

  const handleLabelSubmit = (e) => {
    e.preventDefault();
    if (newLabelName.trim()) createLabelMutation.mutate(newLabelName);
  };

  if (!project) return <div>Loading...</div>;

  return (
    <div className={styles.container}>
      {/* Left Column */}
      <div>
        <div className={styles.card}>
          <h3 className={styles.sectionTitle}>Description</h3>
          <textarea 
            className={styles.descriptionEditor}
            defaultValue={project.description}
            onBlur={(e) => updateMutation.mutate({ description: e.target.value })}
            placeholder="Add project description..."
          />
        </div>

        <div className={styles.card}>
          <h3 className={styles.sectionTitle}>Progress</h3>
          <BurndownChart projectId={id} />
        </div>

        <div className={styles.card}>
           <h3 className={styles.sectionTitle}>Team</h3>
           <div style={{ display:'flex', flexDirection:'column', gap:'0.75rem' }}>
             {members.map(member => (
               <div key={member.id} style={{ display:'flex', alignItems:'center', gap:'0.75rem' }}>
                 <Avatar 
                    src={member.avatar} 
                    fallback={member.username?.[0] || 'U'} // SAFE ACCESS
                    size="sm" 
                 />
                 <div>
                   <div style={{fontWeight:600, fontSize:'0.9rem'}}>{member.first_name} {member.last_name}</div>
                   <div style={{fontSize:'0.75rem', color:'#6b7280'}}>{member.role || 'Member'}</div>
                 </div>
               </div>
             ))}
             {!members.length && <div style={{color:'#9ca3af', fontSize:'0.9rem', fontStyle:'italic'}}>No members assigned.</div>}
           </div>
        </div>
      </div>

      {/* Right Column */}
      <div>
        <div className={styles.card}>
          <h3 className={styles.sectionTitle}>Key Dates</h3>
          <div className={styles.datesGrid}>
            <div>
              <label className="text-xs font-bold text-gray-500 block mb-1">Start Date</label>
              <input 
                type="date" 
                className={styles.dateInput}
                value={project.start_date || ''}
                onChange={(e) => handleDateChange('start_date', e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs font-bold text-gray-500 block mb-1">Due Date</label>
              <input 
                type="date" 
                className={styles.dateInput}
                value={project.end_date || ''}
                onChange={(e) => handleDateChange('end_date', e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className={styles.card}>
          <h3 className={styles.sectionTitle}>Labels</h3>
          <div className={styles.labelsContainer}>
            {labels.map(label => (
              <span key={label.id} className={styles.labelChip} style={{ background: '#eff6ff', color: '#1e40af', border: '1px solid #dbeafe' }}>
                {label.name} 
                <X 
                  size={12} 
                  className="cursor-pointer hover:text-red-500 ml-1" 
                  onClick={() => deleteLabelMutation.mutate(label.id)}
                />
              </span>
            ))}
            
            {!isAddingLabel ? (
              <button className={styles.addLabelBtn} onClick={() => setIsAddingLabel(true)}>
                <Plus size={14} /> Add Label
              </button>
            ) : (
              <form onSubmit={handleLabelSubmit} style={{ display:'flex', alignItems:'center', gap:'0.25rem' }}>
                <input 
                  autoFocus
                  className="text-sm border rounded px-2 py-1 w-24 outline-none"
                  placeholder="Name"
                  value={newLabelName}
                  onChange={(e) => setNewLabelName(e.target.value)}
                  onBlur={() => !newLabelName && setIsAddingLabel(false)}
                />
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectOverview;