import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import styles from './WorkspaceSettingsPage.module.css';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EditWorkspaceModal from '../../components/workspace/EditWorkspaceModal';
import { deleteWorkspace } from '@api/workspaces'; // Assume this API exists
import { fetchWorkspaces } from '@store/slices/workspaceSlice';
import { pushNotification } from '@store/slices/notificationSlice';

export default function WorkspaceSettingsPage() {
  const { workspaceId } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { list: workspaces, loading } = useSelector((s) => s.workspace);
  const workspace = workspaces.find((ws) => ws.id === workspaceId);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  if (loading && !workspace) {
    return <LoadingSpinner />;
  }
  
  if (!workspace) {
    return <div className={styles.notFound}>Workspace not found.</div>;
  }

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to permanently delete the workspace "${workspace.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await deleteWorkspace(workspaceId);
      dispatch(fetchWorkspaces()); // Refresh list
      dispatch(pushNotification({ id: Date.now(), message: `Workspace '${workspace.name}' deleted.` }));
      navigate('/workspaces'); // Navigate to the list page after deletion
    } catch (error) {
      console.error('Workspace deletion failed:', error);
      dispatch(pushNotification({ id: Date.now(), message: `Error deleting workspace: ${error.message || 'Unknown error'}`, type: 'error' }));
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>{workspace.name} Settings</h1>
        <p className={styles.description}>Manage workspace details, membership, and dangerous actions.</p>
      </header>

      <section className={styles.settingsSection}>
        <h2>General Information</h2>
        <div className={styles.settingsCard}>
          <p>Name: <strong>{workspace.name}</strong></p>
          <p>Description: {workspace.description || 'N/A'}</p>
          <button className={styles.actionBtn} onClick={() => setIsEditModalOpen(true)}>Edit Details</button>
        </div>
      </section>

      <section className={styles.settingsSection}>
        <h2>Membership & Roles</h2>
        <div className={styles.settingsCard}>
          <p>Current Members: <strong>{workspace.members?.length || 0}</strong></p>
          <button className={styles.actionBtn} onClick={() => navigate(`/workspaces/${workspaceId}`)}>View & Manage Members</button>
        </div>
      </section>

      <section className={styles.settingsSection}>
        <h2>Danger Zone</h2>
        <div className={`${styles.settingsCard} ${styles.dangerCard}`}>
          <h3>Delete Workspace</h3>
          <p>Permanently delete this workspace and all associated data, including projects, tasks, and files.</p>
          <button className={styles.deleteBtn} onClick={handleDelete}>Delete Workspace</button>
        </div>
      </section>

      <EditWorkspaceModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        workspace={workspace}
      />
    </div>
  );
}