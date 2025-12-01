import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Settings } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { api } from '../../services/api';
import CreateWorkspaceModal from './CreateWorkspaceModal';
import Button from '../../components/ui/Button/Button';
import styles from './WorkspaceHeader.module.css';

const WorkspaceHeader = () => {
  const { currentWorkspace } = useWorkspace();
  const [showSettings, setShowSettings] = useState(false);

  // Fetch stats dependent on current workspace
  const { data: stats } = useQuery({
    queryKey: ['workspaceStats', currentWorkspace?.id],
    queryFn: async () => {
      if (!currentWorkspace) return null;
      const res = await api.get(`/workspaces/${currentWorkspace.id}/stats/`);
      return res.data;
    },
    enabled: !!currentWorkspace
  });

  if (!currentWorkspace) return null;

  return (
    <div className={styles.container}>
      <div className={styles.left}>
        <div className={styles.titleRow}>
          <h1 className={styles.title}>{currentWorkspace.name}</h1>
          <Button 
            variant="ghost" 
            className={styles.settingsButton}
            onClick={() => setShowSettings(true)}
          >
            <Settings size={20} />
          </Button>
        </div>
        <p className={styles.subtitle}>{currentWorkspace.description || 'Manage your projects effectively'}</p>
      </div>

      <div className={styles.statsRow}>
        <div className={styles.statCard}>
          <span className={styles.statValue}>{stats?.active_projects || 0}</span>
          <span className={styles.statLabel}>Active Projects</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statValue}>{stats?.members_count || 1}</span>
          <span className={styles.statLabel}>Team Members</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statValue}>{stats?.upcoming_deadlines || 0}</span>
          <span className={styles.statLabel}>Deadlines</span>
        </div>
      </div>

      {showSettings && (
        <CreateWorkspaceModal 
          initialData={currentWorkspace} 
          onClose={() => setShowSettings(false)} 
        />
      )}
    </div>
  );
};

export default WorkspaceHeader;