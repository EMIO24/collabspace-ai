import React from 'react';
import AnalyticsDashboard from '../features/analytics/AnalyticsDashboard';
import TimeReportTable from '../features/analytics/TimeReportTable';
import { useWorkspace } from '../context/WorkspaceContext';
import styles from './AnalyticsPage.module.css';

const AnalyticsPage = () => {
  const { currentWorkspace } = useWorkspace();

  if (!currentWorkspace) {
    return <div className={styles.emptyState}>Please select a workspace.</div>;
  }

  return (
    <div className={styles.container}>
      {/* The new Dashboard handles Metrics and Charts */}
      <AnalyticsDashboard />
      
      {/* Detailed Time Report Table below */}
      <div className={styles.reportSection}>
        <h3 className={styles.sectionTitle}>Detailed Time Logs</h3>
        <TimeReportTable workspaceId={currentWorkspace.id} />
      </div>
    </div>
  );
};

export default AnalyticsPage;