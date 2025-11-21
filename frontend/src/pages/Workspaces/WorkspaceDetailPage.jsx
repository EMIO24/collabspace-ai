import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchWorkspaces, setCurrentWorkspace } from '@store/slices/workspaceSlice';
import styles from './WorkspaceDetailPage.module.css';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import MembersList from '../../components/workspace/MembersList';
// import { fetchWorkspaceDetails } from '@api/workspaces'; // Assume this API exists

export default function WorkspaceDetailPage() {
  const { workspaceId } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { list: workspaces, loading } = useSelector((s) => s.workspace);

  const workspace = workspaces.find((ws) => ws.id === workspaceId);

  useEffect(() => {
    if (!workspace && !loading) {
      // If the workspace isn't in the list, fetch all workspaces or a specific one
      dispatch(fetchWorkspaces());
    }
  }, [workspaceId, workspace, loading, dispatch]);

  if (loading || !workspace) {
    // Show spinner if loading or if we haven't found the workspace yet
    return <LoadingSpinner />;
  }

  // Set the current workspace when viewing its detail page
  dispatch(setCurrentWorkspace(workspace));

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>{workspace.name}</h1>
        <p className={styles.description}>{workspace.description || 'No description provided.'}</p>
        <button className={styles.settingsBtn} onClick={() => navigate(`/workspaces/${workspaceId}/settings`)}>
          Workspace Settings
        </button>
      </header>
      
      <section className={styles.stats}>
        {/* Placeholder for real stats */}
        <div className={styles.statCard}>
          <h3>34 Projects</h3>
          <p>Active and archived</p>
        </div>
        <div className={styles.statCard}>
          <h3>1.2k Tasks</h3>
          <p>Total items</p>
        </div>
        <div className={styles.statCard}>
          <h3>15 Members</h3>
          <p>Currently active</p>
        </div>
      </section>

      <section className={styles.membersSection}>
        <h2>Team Members</h2>
        {/* Assume workspace object includes members: [{ id, name, role }] */}
        <MembersList members={workspace.members || []} />
      </section>
    </div>
  );
}