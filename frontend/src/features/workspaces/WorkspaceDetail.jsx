import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Settings, Users, Star, UserPlus, FolderOpen, 
  BarChart2, Grid, MoreVertical, LayoutGrid
} from 'lucide-react';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import { toast } from 'react-hot-toast';
import styles from './WorkspaceDetail.module.css';

// Child Tabs
import WorkspaceOverview from './tabs/WorkspaceOverview';
import WorkspaceProjectsList from './tabs/WorkspaceProjectsList';
import WorkspaceMembers from './tabs/WorkspaceMembers'; 
import WorkspaceSettings from './settings/WorkspaceSettings'; 
// import AnalyticsDashboard from '../analytics/AnalyticsDashboard'; // Analytics Removed

const TABS = {
  OVERVIEW: 'Overview',
  PROJECTS: 'Projects',
  MEMBERS: 'Members',
  SETTINGS: 'Settings'
};

const WorkspaceDetail = () => {
  const { id } = useParams();
  const { setCurrentWorkspace } = useWorkspace();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState(TABS.OVERVIEW);
  
  // 1. Fetch Workspace Data
  const { data: workspace, isLoading } = useQuery({
    queryKey: ['workspace', id],
    queryFn: async () => {
      const res = await api.get(`/workspaces/${id}/`);
      setCurrentWorkspace(res.data);
      return res.data;
    },
    enabled: !!id,
    staleTime: 60000 // Cache for 1 minute to prevent 429s on navigation
  });
  
  // 2. Fetch Members (For Avatars in Header)
  const { data: members } = useQuery({
    queryKey: ['workspaceMembers', id],
    queryFn: async () => {
       const res = await api.get(`/workspaces/${id}/members/`);
       return Array.isArray(res.data) ? res.data : (res.data.results || []);
    },
    enabled: !!id,
    staleTime: 60000
  });

  // Actions
  const updateMutation = useMutation({
    mutationFn: (data) => api.put(`/workspaces/${id}/`, data),
    onSuccess: () => {
        queryClient.invalidateQueries(['workspace', id]);
        toast.success('Workspace updated');
    }
  });

  const handleNameBlur = (e) => {
      if (workspace && e.target.value !== workspace.name) {
          updateMutation.mutate({ name: e.target.value });
      }
  };

  const getWorkspaceIcon = (name) => {
    const lower = name?.toLowerCase() || '';
    if (lower.includes('design')) return '🎨';
    if (lower.includes('dev')) return '👨‍💻';
    return '🏢';
  };

  if (isLoading) return <div className={styles.loading}>Loading...</div>;
  if (!workspace) return <div className={styles.loading}>Workspace not found</div>;

  return (
    <div className={styles.container}>
      
      {/* PROFESSIONAL BANNER */}
      <div className={styles.banner}>
         <div className={styles.bannerContent}>
            <div className={styles.bannerLeft}>
               <div className={styles.workspaceIcon}>
                  {getWorkspaceIcon(workspace.name)}
               </div>
               <div className={styles.workspaceInfo}>
                  <input 
                     defaultValue={workspace.name}
                     className={styles.nameInput}
                     onBlur={handleNameBlur}
                  />
                  <div className={styles.metaRow}>
                     <span className={styles.badge}>{workspace.role || 'Member'}</span>
                     <span>•</span>
                     <span>{members?.length || 1} Members</span>
                     <div className={styles.avatarStack}>
                        {members?.slice(0, 4).map((m, index) => (
                           <img 
                              // FIX: Use unique ID or fallback to index to prevent key warning
                              key={m.id || `member-${index}`} 
                              src={m.avatar || `https://ui-avatars.com/api/?name=${m.username || 'U'}&background=random`} 
                              className={styles.stackItem} 
                              alt="user"
                           />
                        ))}
                     </div>
                  </div>
                  {workspace.description && <p className={styles.description}>{workspace.description}</p>}
               </div>
            </div>

            <div className={styles.bannerRight}>
               <div className={styles.actionGroup}>
                  <button className={styles.headerBtn} onClick={() => setActiveTab(TABS.SETTINGS)}>
                     <Settings size={18} /> Settings
                  </button>
                  <button className={`${styles.headerBtn} ${styles.primaryBtn}`} onClick={() => setActiveTab(TABS.MEMBERS)}>
                     <UserPlus size={18} /> Invite
                  </button>
                  <button 
                    className={styles.headerBtn} 
                    onClick={() => updateMutation.mutate({ is_favorite: !workspace.is_favorite })}
                  >
                    <Star size={18} className={workspace.is_favorite ? styles.starActive : ''} />
                  </button>
               </div>
            </div>
         </div>
      </div>

      {/* TABS NAVIGATION */}
      <div className={styles.tabsContainer}>
         <div className={styles.tabsInner}>
            {Object.values(TABS).map(tab => (
               <button 
                  key={tab} 
                  className={`${styles.tab} ${activeTab === tab ? styles.activeTab : ''}`}
                  onClick={() => setActiveTab(tab)}
               >
                  {tab}
               </button>
            ))}
         </div>
      </div>

      {/* DYNAMIC CONTENT */}
      <div className={styles.content}>
         <div className={styles.contentInner}>
            {activeTab === TABS.OVERVIEW && (
                <WorkspaceOverview workspaceId={id} onTabChange={setActiveTab} />
            )}
            {activeTab === TABS.PROJECTS && (
                <WorkspaceProjectsList workspaceId={id} />
            )}
            {activeTab === TABS.MEMBERS && (
                // FIX: Pass workspaceId explicitly to prevent 404 undefined error
                <WorkspaceMembers workspaceId={id} /> 
            )}
            {activeTab === TABS.SETTINGS && (
                <WorkspaceSettings />
            )}
         </div>
      </div>

    </div>
  );
};

export default WorkspaceDetail;