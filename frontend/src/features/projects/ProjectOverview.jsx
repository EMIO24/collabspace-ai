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
  
  // 1. Fetch Project
  const { data: project } = useQuery({
    queryKey: ['project', id],
    queryFn: async () => (await api.get(`/projects/${id}/`)).data
  });

  // 2. Fetch Labels (Data Normalization Fix)
  const { data: rawLabels } = useQuery({
    queryKey: ['projectLabels', id],
    queryFn: async () => (await api.get(`/projects/${id}/labels/`)).data || []
  });

  const labels = useMemo(() => {
    if (!rawLabels) return [];
    if (Array.isArray(rawLabels)) return rawLabels;
    if (rawLabels.results && Array.isArray(rawLabels.results)) return rawLabels.results;
    return [];
  }, [rawLabels]);

  // 3. Fetch Members (Data Normalization Fix)
  const { data: rawMembers } = useQuery({
    queryKey: ['projectMembers', id],
    queryFn: async () => (await api.get(`/projects/${id}/members/`)).data
  });

  const members = useMemo(() => {
    if (!rawMembers) return [];
    if (Array.isArray(rawMembers)) return rawMembers;
    if (rawMembers.results && Array.isArray(rawMembers.results)) return rawMembers.results;
    return [];
  }, [rawMembers]);

  // --- MUTATIONS ---
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
  const stats = project?.statistics || {};

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
            placeholder="Add project description (Markdown supported)..."
          />
        </div>

        <div className={styles.card}>
          <h3 className={styles.sectionTitle}>Progress</h3>
          <BurndownChart projectId={id} />
        </div>

        <div className={styles.card}>
           <h3 className={styles.sectionTitle}>Team</h3>
           <div className="flex flex-col gap-3">
             {members.map(member => (
               <div key={member.id} className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded-lg transition-colors">
                 <Avatar 
                    src={member.avatar} 
                    /* FIX: Safe access to username string to prevent crash */
                    fallback={(member.username && member.username.length > 0) ? member.username[0].toUpperCase() : 'U'} 
                    size="sm" 
                 />
                 <div>
                   <div className="font-medium text-gray-800">{member.first_name} {member.last_name}</div>
                   <div className="text-xs text-gray-500">{member.role || 'Member'}</div>
                 </div>
               </div>
             ))}
             {!members.length && <div className="text-gray-400 text-sm italic">No members assigned.</div>}
           </div>
        </div>
      </div>

      {/* Right Column */}
      <div>
        {/* Quick Stats extracted from Project JSON */}
        <div className={styles.card}>
           <h3 className={styles.sectionTitle}>Stats</h3>
           <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-blue-50 rounded-lg">
                 <div className="text-xs text-gray-500 font-bold uppercase">Total Tasks</div>
                 <div className="text-2xl font-bold text-blue-600">{stats.total_tasks || 0}</div>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                 <div className="text-xs text-gray-500 font-bold uppercase">Completed</div>
                 <div className="text-2xl font-bold text-green-600">{stats.completed_tasks || 0}</div>
              </div>
              <div className="p-3 bg-orange-50 rounded-lg">
                 <div className="text-xs text-gray-500 font-bold uppercase">Pending</div>
                 <div className="text-2xl font-bold text-orange-600">{stats.pending_tasks || 0}</div>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg">
                 <div className="text-xs text-gray-500 font-bold uppercase">Members</div>
                 <div className="text-2xl font-bold text-purple-600">{stats.total_members || 1}</div>
              </div>
           </div>
        </div>

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
              <form onSubmit={handleLabelSubmit} className="flex items-center gap-1">
                <input 
                  autoFocus
                  className="text-sm border rounded px-2 py-1 w-24 outline-none focus:border-blue-500"
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