import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchWorkspaces, setCurrentWorkspace } from '@store/slices/workspaceSlice';
import styles from './WorkspaceListPage.module.css';
import WorkspaceCard from '../../components/workspace/WorkspaceCard';
import CreateWorkspaceModal from '../../components/workspace/CreateWorkspaceModal';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { pushNotification } from '@store/slices/notificationSlice';

export default function WorkspaceListPage() {
  const dispatch = useDispatch();
  const { list: workspaces, loading, error, current: currentWorkspace } = useSelector((s) => s.workspace);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    if (workspaces.length === 0 && !loading) {
      dispatch(fetchWorkspaces());
    }
  }, [dispatch, workspaces.length, loading]);

  const handleSelectWorkspace = (workspace) => {
    dispatch(setCurrentWorkspace(workspace));
    dispatch(pushNotification({ id: Date.now(), message: `Switched to workspace: ${workspace.name}` }));
    // In a real app, you would navigate away here, e.g., to /dashboard
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <div className={styles.error}>Error loading workspaces: {error.message || error}</div>;
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h2>Your Workspaces</h2>
        <button className={styles.createBtn} onClick={() => setIsModalOpen(true)}>
          + Create New Workspace
        </button>
      </header>

      <div className={styles.list}>
        {workspaces.map((ws) => (
          <WorkspaceCard
            key={ws.id}
            workspace={ws}
            isSelected={currentWorkspace?.id === ws.id}
            onSelect={handleSelectWorkspace}
          />
        ))}
      </div>

      <CreateWorkspaceModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
  );
}