import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  MoreVertical, Edit3, Settings, Star, LogOut, Trash2, 
  Calendar, User, Activity, LayoutGrid, Users, Mail, BarChart3 
} from 'lucide-react';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import { toast } from 'react-hot-toast';
import styles from './WorkspaceDetail.module.css';

// Tabs
import WorkspaceOverview from './tabs/WorkspaceOverview';
import WorkspaceProjectsList from './tabs/WorkspaceProjectsList';
import WorkspaceMembers from './tabs/WorkspaceMembers';
import WorkspaceSettingsTab from './tabs/WorkspaceSettingsTab';
import WorkspaceInvites from './tabs/WorkspaceInvites';
import WorkspaceAnalyticsTab from './tabs/WorkspaceAnalyticsTab';

const TABS = {
  OVERVIEW: 'Overview',
  PROJECTS: 'Projects',
  MEMBERS: 'Members',
  INVITES: 'Invitations',
  ANALYTICS: 'Analytics',
  SETTINGS: 'Settings'
};

const WorkspaceDetail = () => {
  const { id } = useParams();
  const { setCurrentWorkspace } = useWorkspace();
  const [activeTab, setActiveTab] = useState(TABS.OVERVIEW);
  const [showMenu, setShowMenu] = useState(false);
  const [isStarred, setIsStarred] = useState(false);
  const menuRef = useRef(null);
  const navigate = useNavigate();

  const { data: workspace, isLoading } = useQuery({
    queryKey: ['workspace', id],
    queryFn: async () => {
      const res = await api.get(`/workspaces/${id}/`);
      setCurrentWorkspace(res.data);
      setIsStarred(res.data.is_favorite || false);
      return res.data;
    },
    enabled: !!id
  });

  const { data: members } = useQuery({
    queryKey: ['workspaceHeaderMembers', id],
    queryFn: async () => {
      const res = await api.get(`/workspaces/${id}/members/`);
      return Array.isArray(res.data) ? res.data : (res.data.results || []);
    },
    enabled: !!id
  });

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const starMutation = useMutation({
    mutationFn: () => api.post(`/workspaces/${id}/favorite/`), 
    onMutate: () => {
        setIsStarred(!isStarred);
        toast.success(isStarred ? "Removed from favorites" : "Added to favorites");
    },
    onError: () => setIsStarred(!isStarred)
  });

  const leaveMutation = useMutation({
    mutationFn: () => api.delete(`/workspaces/${id}/members/me/`),
    onSuccess: () => {
        toast.success("Left workspace");
        navigate('/workspaces');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`/workspaces/${id}/`),
    onSuccess: () => {
        toast.success("Workspace deleted");
        navigate('/workspaces');
    }
  });

  if (isLoading) return <div className="p-10 text-center text-gray-500">Loading workspace...</div>;
  if (!workspace) return <div className="p-10 text-center text-gray-500">Workspace not found</div>;

  const isOwner = true; 

  return (
    <div className={styles.container}>
      <div className={styles.banner}>
        <div className={styles.bannerContent}>
          <div className={styles.bannerLeft}>
            <div className={styles.workspaceIcon}>
              {workspace.name.toLowerCase().includes('design') ? '🎨' : 
               workspace.name.toLowerCase().includes('market') ? '📈' : '🚀'}
            </div>
            <div className={styles.workspaceInfo}>
              <h1 className={styles.title}>
                {workspace.name}
                {isStarred && <Star className={styles.starIcon} fill="currentColor" />}
              </h1>
              <p className={styles.description}>{workspace.description || 'Collaborate on creative projects.'}</p>
              
              <div className={styles.metaRow}>
                <div className={styles.avatarStack}>
                   {members?.slice(0, 4).map((m, i) => (
                     // FIX: Added Unique Key here
                     <div key={m.id || i} className={styles.avatar} title={m.email}>
                        {m.avatar ? <img src={m.avatar} alt="user" className="w-full h-full object-cover rounded-full"/> : (m.username?.[0] || 'U').toUpperCase()}
                     </div>
                   ))}
                   {(members?.length > 4) && (
                     <div 
                        className={`${styles.avatar} ${styles.avatarCount}`}
                        onClick={() => setActiveTab(TABS.MEMBERS)}
                     >
                        +{members.length - 4}
                     </div>
                   )}
                </div>
              </div>
            </div>
          </div>

          <div className={styles.bannerRight}>
            <div className={styles.bannerActions}>
                <button className={styles.inviteBtn} onClick={() => setActiveTab(TABS.INVITES)}>
                Invite
                </button>
                
                <div className={styles.menuWrapper} ref={menuRef}>
                    <button className={styles.menuBtn} onClick={() => setShowMenu(!showMenu)}>
                        <MoreVertical size={20} />
                    </button>

                    {showMenu && (
                        <div className={styles.dropdown}>
                            <button className={styles.dropdownItem} onClick={() => { setActiveTab(TABS.SETTINGS); setShowMenu(false); }}>
                                <Edit3 size={16} /> Edit Workspace
                            </button>
                            <button className={styles.dropdownItem} onClick={() => { setActiveTab(TABS.SETTINGS); setShowMenu(false); }}>
                                <Settings size={16} /> Settings
                            </button>
                            <button className={styles.dropdownItem} onClick={() => { starMutation.mutate(); setShowMenu(false); }}>
                                <Star size={16} fill={isStarred ? "currentColor" : "none"} /> {isStarred ? 'Unstar' : 'Star'}
                            </button>
                            <div className={styles.divider} />
                            <button className={styles.dropdownItem} onClick={() => { if(confirm("Leave workspace?")) leaveMutation.mutate(); }}>
                                <LogOut size={16} /> Leave Workspace
                            </button>
                            {isOwner && (
                                <button className={`${styles.dropdownItem} ${styles.dangerItem}`} onClick={() => { 
                                    setActiveTab(TABS.SETTINGS); 
                                    setShowMenu(false); 
                                    toast("Please scroll to Danger Zone to delete", { icon: 'ℹ️' });
                                }}>
                                    <Trash2 size={16} /> Delete Workspace
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>
          </div>
        </div>
      </div>

      <div className={styles.tabsContainer}>
        <div className={styles.tabsInner}>
          {Object.values(TABS).map((tab) => (
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

      <div className={styles.content}>
        <div className={styles.contentInner}>
          {activeTab === TABS.OVERVIEW && <WorkspaceOverview workspaceId={id} onTabChange={setActiveTab} />}
          {activeTab === TABS.PROJECTS && <WorkspaceProjectsList workspaceId={id} />}
          {activeTab === TABS.MEMBERS && <WorkspaceMembers workspaceId={id} />}
          {activeTab === TABS.INVITES && <WorkspaceInvites workspaceId={id} />}
          {activeTab === TABS.ANALYTICS && <WorkspaceAnalyticsTab workspaceId={id} />}
          {activeTab === TABS.SETTINGS && <WorkspaceSettingsTab workspaceId={id} initialData={workspace} />}
        </div>
      </div>

    </div>
  );
};

export default WorkspaceDetail;