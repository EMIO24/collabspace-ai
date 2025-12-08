import React, { useState } from 'react';
import { Outlet, NavLink, useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  LayoutTemplate, KanbanSquare, ListTodo, FolderOpen, History, Settings, 
  Star, MoreHorizontal, ChevronDown, PieChart
} from 'lucide-react';
import { api } from '../../services/api';
import styles from './ProjectLayout.module.css';
import { toast } from 'react-hot-toast';

const ProjectLayout = () => {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Fetch Project Data
  const { data: project } = useQuery({
    queryKey: ['project', id],
    queryFn: async () => (await api.get(`/projects/${id}/`)).data,
    enabled: !!id
  });

  const updateMutation = useMutation({
    mutationFn: (data) => api.put(`/projects/${id}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['project', id]);
      toast.success('Project updated');
    }
  });

  const handleNameBlur = (e) => {
    if (project && e.target.value !== project.name) {
      updateMutation.mutate({ name: e.target.value });
    }
  };

  const handleStatusChange = (e) => {
    updateMutation.mutate({ status: e.target.value });
  };

  if (!project) return <div className={styles.loading}>Loading...</div>;

  return (
    <div className={styles.container}>
      {/* Rich Header */}
      <div className={styles.header}>
        <div className={styles.headerTop}>
          <div className={styles.projectIdentity}>
            <div className={styles.projectIcon}>🚀</div>
            <div className={styles.nameContainer}>
               <input 
                 defaultValue={project.name}
                 className={styles.nameInput}
                 onBlur={handleNameBlur}
               />
               <span className={styles.lastUpdated}>Last updated today</span>
            </div>
          </div>

          <div className={styles.headerActions}>
             <div className={styles.selectWrapper}>
               <select 
                  className={styles.statusSelect} 
                  value={project.status}
                  onChange={handleStatusChange}
               >
                  <option value="active">In Progress</option>
                  <option value="on_hold">On Hold</option>
                  <option value="completed">Completed</option>
               </select>
               <ChevronDown size={14} className={styles.selectIcon} />
             </div>

             <button 
                className={`${styles.actionBtn} ${project.is_favorite ? styles.starBtn : ''}`}
                onClick={() => updateMutation.mutate({ is_favorite: !project.is_favorite })}
             >
                <Star size={20} fill={project.is_favorite ? "currentColor" : "none"} />
             </button>
             
             <button className={styles.actionBtn}>
                <MoreHorizontal size={20} />
             </button>
          </div>
        </div>

        {/* Tabs */}
        <div className={styles.tabs}>
          <NavLink to={`/projects/${id}`} end className={({ isActive }) => `${styles.tab} ${isActive ? styles.activeTab : ''}`}>
            Overview
          </NavLink>
          <NavLink to={`/projects/${id}/board`} className={({ isActive }) => `${styles.tab} ${isActive ? styles.activeTab : ''}`}>
            Tasks (Board)
          </NavLink>
          <NavLink to={`/projects/${id}/list`} className={({ isActive }) => `${styles.tab} ${isActive ? styles.activeTab : ''}`}>
            Tasks (List)
          </NavLink>
          <NavLink to={`/projects/${id}/files`} className={({ isActive }) => `${styles.tab} ${isActive ? styles.activeTab : ''}`}>
            Files
          </NavLink>
          <NavLink to={`/projects/${id}/analytics`} className={({ isActive }) => `${styles.tab} ${isActive ? styles.activeTab : ''}`}>
            Analytics
          </NavLink>
          <NavLink to={`/projects/${id}/activity`} className={({ isActive }) => `${styles.tab} ${isActive ? styles.activeTab : ''}`}>
            Activity
          </NavLink>
          <NavLink to={`/projects/${id}/settings`} className={({ isActive }) => `${styles.tab} ${isActive ? styles.activeTab : ''}`}>
            Settings
          </NavLink>
        </div>
      </div>

      <div className={styles.content}>
        <Outlet />
      </div>
    </div>
  );
};

export default ProjectLayout;