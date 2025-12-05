import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Plus, MoreHorizontal, Search, LayoutGrid, List, 
  Briefcase, Rocket, Palette, Mail 
} from 'lucide-react';
import { api } from '../services/api';
import { useWorkspace } from '../context/WorkspaceContext';
import CreateWorkspaceModal from '../features/workspaces/CreateWorkspaceModal';
import Avatar from '../components/ui/Avatar/Avatar';
import styles from './WorkspacesPage.module.css';
import { toast } from 'react-hot-toast';

const ICONS_MAP = {
  'design': '🎨',
  'marketing': '💼',
  'startup': '🚀',
  'default': '🏢'
};

const WorkspacesPage = () => {
  const { setCurrentWorkspace } = useWorkspace();
  const [viewMode, setViewMode] = useState('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // 1. Fetch Workspaces
  const { data: rawData, isLoading } = useQuery({
    queryKey: ['workspaces', searchQuery],
    queryFn: async () => {
      const endpoint = searchQuery 
        ? `/workspaces/search/?q=${searchQuery}` 
        : '/workspaces/';
      const res = await api.get(endpoint);
      return res.data;
    }
  });

  const workspaces = useMemo(() => {
    if (!rawData) return [];
    if (Array.isArray(rawData)) return rawData;
    if (rawData.results && Array.isArray(rawData.results)) return rawData.results;
    return [];
  }, [rawData]);

  // 2. Fetch Invitations (Placeholder for now)
  const { data: invitations } = useQuery({
    queryKey: ['pendingInvitations'],
    queryFn: async () => [] // Mock empty
  });

  const handleCardClick = (ws) => {
    setCurrentWorkspace(ws);
    navigate(`/workspaces/${ws.id}`);
  };

  const getIcon = (name) => {
    const lower = name.toLowerCase();
    if (lower.includes('design')) return ICONS_MAP.design;
    if (lower.includes('market')) return ICONS_MAP.marketing;
    if (lower.includes('lab') || lower.includes('tech')) return ICONS_MAP.startup;
    return ICONS_MAP.default;
  };

  return (
    <div className={styles.container}>
      
      {/* Pending Invitations Banner */}
      {invitations?.length > 0 && (
        <div className={styles.inviteBanner}>
          <div className={styles.inviteText}>
            <Mail size={20} />
            You have {invitations.length} pending invitations to join workspaces.
          </div>
          <div className={styles.inviteActions}>
             <button className={styles.acceptBtn}>Review</button>
          </div>
        </div>
      )}

      {/* Header */}
      <div className={styles.header}>
        <div className={styles.titleGroup}>
          <h1>Workspaces</h1>
          <div className={styles.subtitle}>Manage your teams and projects</div>
        </div>

        <div className={styles.controls}>
          <div className={styles.searchWrapper}>
            <Search size={16} className={styles.searchIcon} />
            <input 
              type="text" 
              placeholder="Search..." 
              className={styles.searchInput}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className={styles.viewToggle}>
            <button 
              className={`${styles.toggleBtn} ${viewMode === 'grid' ? styles.activeToggle : ''}`}
              onClick={() => setViewMode('grid')}
            >
              <LayoutGrid size={16} /> Grid
            </button>
            <button 
              className={`${styles.toggleBtn} ${viewMode === 'list' ? styles.activeToggle : ''}`}
              onClick={() => setViewMode('list')}
            >
              <List size={16} /> List
            </button>
          </div>

          <button className={styles.createBtn} onClick={() => setIsModalOpen(true)}>
            <Plus size={18} /> New
          </button>
        </div>
      </div>

      {/* Content View */}
      {isLoading ? (
        <div className="p-8 text-center text-gray-400">Loading workspaces...</div>
      ) : workspaces.length === 0 ? (
        <div className={styles.emptyState}>
          <h3>No workspaces found</h3>
          <p>Create your first workspace to get started.</p>
        </div>
      ) : viewMode === 'grid' ? (
        
        /* --- GRID VIEW (3 Per Row) --- */
        <div className={styles.grid}>
          {workspaces.map((ws) => (
            <div key={ws.id} className={styles.card} onClick={() => handleCardClick(ws)}>
              
              <div className={styles.cardHeader}>
                <div className={styles.cardIcon}>{getIcon(ws.name)}</div>
                <button className={styles.menuBtn} onClick={(e) => e.stopPropagation()}>
                  <MoreHorizontal size={20} />
                </button>
              </div>
              
              <div className="mb-4">
                <h3 className={styles.cardTitle}>{ws.name}</h3>
                <p className={styles.cardDesc}>
                  {ws.description || 'No description provided for this team.'}
                </p>
              </div>

              <div className={styles.membersSection}>
                <div className={styles.avatarStack}>
                   {/* Real Member Rendering */}
                   {ws.members && ws.members.length > 0 ? (
                     <>
                        {ws.members.slice(0, 3).map((m) => (
                          <div key={m.id} className={styles.avatar} title={m.username}>
                             {m.avatar ? <img src={m.avatar} alt={m.username} className="w-full h-full rounded-full object-cover" /> : m.username?.[0]?.toUpperCase()}
                          </div>
                        ))}
                        {ws.members.length > 3 && (
                          <div className={styles.avatar} style={{ background: '#f3f4f6', color: '#6b7280', fontSize: '0.7rem' }}>
                            +{ws.members.length - 3}
                          </div>
                        )}
                     </>
                   ) : (
                      // Fallback for when members array isn't populated in list view
                      <div className={styles.avatar} style={{ background: '#e0e7ff', color: '#6366f1' }}>
                        {ws.name?.[0]}
                      </div>
                   )}
                </div>
                <span className={styles.metaText}>
                  {ws.members_count || 1} members
                </span>
              </div>

              <div className={styles.cardFooter}>
                <span className={styles.roleLabel}>
                   {ws.role === 'owner' ? 'Owner' : 'Member'}
                </span>
                <span className={styles.projectCount}>
                   {ws.projects_count || 0} Projects
                </span>
              </div>

            </div>
          ))}
        </div>

      ) : (
        /* --- LIST VIEW --- */
        <div className={styles.listView}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Owner</th>
                <th>Members</th>
                <th>Projects</th>
                <th>Role</th>
                <th style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {workspaces.map((ws) => (
                <tr key={ws.id} className={styles.tableRow} onClick={() => handleCardClick(ws)}>
                  <td style={{ fontWeight: 600 }}>{ws.name}</td>
                  <td>{ws.role === 'owner' ? 'You' : (ws.owner_name || 'Admin')}</td>
                  <td>{ws.members_count || '-'}</td>
                  <td>{ws.projects_count || '-'}</td>
                  <td>
                    <span style={{ padding: '2px 8px', background: '#eff6ff', color: '#1d4ed8', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600 }}>
                      {ws.role || 'Member'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button className={styles.menuBtn} onClick={(e) => e.stopPropagation()}>
                      <MoreHorizontal size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isModalOpen && <CreateWorkspaceModal onClose={() => setIsModalOpen(false)} />}
    </div>
  );
};

export default WorkspacesPage;