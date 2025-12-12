import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { 
  Plus, Users, FolderKanban, ArrowRight, LayoutGrid, RefreshCw, AlertCircle 
} from 'lucide-react';
import { api } from '../services/api';
import { useWorkspace } from '../context/WorkspaceContext';
import Button from '../components/ui/Button/Button';
import CreateWorkspaceModal from '../features/workspaces/CreateWorkspaceModal';
import styles from './WorkspacesPage.module.css';

const WorkspacesPage = () => {
  const navigate = useNavigate();
  const { setCurrentWorkspace } = useWorkspace();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { 
    data: workspaces, 
    isLoading, 
    isError, 
    error, 
    refetch 
  } = useQuery({
    queryKey: ['workspaces'],
    queryFn: async () => {
      const res = await api.get('/workspaces/');
      return Array.isArray(res.data) ? res.data : (res.data.results || []);
    },
    // FIX: Ensure we don't use stale data from a pre-login state
    staleTime: 0,
    refetchOnMount: true,
    retry: 2
  });

  // Effect: Force refetch on mount to handle login redirect timing issues
  useEffect(() => {
    refetch();
  }, [refetch]);

  const handleWorkspaceClick = (workspace) => {
    setCurrentWorkspace(workspace);
    navigate(`/workspaces/${workspace.id}`);
  };

  const getWorkspaceIcon = (name) => {
    const lower = name.toLowerCase();
    if (lower.includes('design') || lower.includes('art')) return '🎨';
    if (lower.includes('market') || lower.includes('sales')) return '📈';
    if (lower.includes('dev') || lower.includes('code') || lower.includes('tech')) return '👨‍💻';
    if (lower.includes('video') || lower.includes('media')) return '🎥';
    if (lower.includes('support')) return '🎧';
    return '🏤';
  };

  if (isLoading) {
    return (
      <div className={styles.loading}>
         <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
         Loading workspaces...
      </div>
    );
  }

  // Error State Handling
  if (isError) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
            <div className={styles.titleGroup}>
              <h1>Workspaces</h1>
            </div>
        </div>
        <div className={styles.emptyState} style={{ borderColor: '#fca5a5', background: '#fef2f2' }}>
           <AlertCircle size={48} className="text-red-400 mb-2" />
           <h3 className="text-red-800">Unable to load workspaces</h3>
           <p className="text-red-600 mb-4">{error?.response?.data?.detail || "Please check your connection and try again."}</p>
           <Button onClick={() => refetch()} variant="outline" className="border-red-200 hover:bg-red-50 text-red-700">
              <RefreshCw size={16} className="mr-2" /> Retry
           </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.titleGroup}>
          <h1>Workspaces</h1>
          <p className={styles.subtitle}>Manage your teams and organization units.</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus size={18} className="mr-2" /> Create Workspace
        </Button>
      </div>

      {/* Grid */}
      <div className={styles.grid}>
        {workspaces && workspaces.length > 0 ? (
          workspaces.map((ws, index) => (
            <div 
              key={ws.id} 
              className={styles.card}
              onClick={() => handleWorkspaceClick(ws)}
            >
              <div className={styles.cardHeader}>
                 <div className={styles.iconWrapper}>
                    {getWorkspaceIcon(ws.name)}
                 </div>
                 <ArrowRight size={20} className={styles.arrowIcon} />
              </div>
              
              <div>
                 <h3 className={styles.cardTitle}>{ws.name}</h3>
                 <span className={styles.roleBadge}>{ws.role || 'Member'}</span>
              </div>

              <div className={styles.statsRow}>
                 <div className={styles.statItem}>
                    <Users size={16} /> 
                    <span>{ws.member_count || 1} Members</span>
                 </div>
                 <div className={styles.statItem}>
                    <FolderKanban size={16} /> 
                    <span>{ws.project_count || 0} Projects</span>
                 </div>
              </div>
            </div>
          ))
        ) : (
          <div className={styles.emptyState}>
             <LayoutGrid size={48} className="text-gray-300 mb-2" />
             <h3>No workspaces found</h3>
             <p className="text-sm text-gray-500 mb-4">Create your first workspace to get started.</p>
             <div className="flex gap-2">
                <Button onClick={() => setIsModalOpen(true)}>Create Workspace</Button>
                <Button variant="ghost" onClick={() => refetch()}><RefreshCw size={16}/></Button>
             </div>
          </div>
        )}
      </div>

      {isModalOpen && (
        <CreateWorkspaceModal onClose={() => setIsModalOpen(false)} />
      )}
    </div>
  );
};

export default WorkspacesPage;