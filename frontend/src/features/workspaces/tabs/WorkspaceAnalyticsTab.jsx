import React from 'react';
import WorkspaceMetrics from '../../analytics/WorkspaceMetrics';
import TeamProductivity from '../../analytics/TeamProductivity';
import TimeReportTable from '../../analytics/TimeReportTable';
import styles from './WorkspaceAnalyticsTab.module.css';

const WorkspaceAnalyticsTab = ({ workspaceId }) => {
  return (
    <div className={styles.container}>
      <div>
        <h3 className={styles.sectionTitle}>Performance Metrics</h3>
        <WorkspaceMetrics workspaceId={workspaceId} />
      </div>

      <div className={styles.grid}>
        <div className={styles.chartCard}>
           <h3 className={styles.sectionTitle}>Team Velocity</h3>
           {/* TeamProductivity uses WorkspaceContext internally */}
           <TeamProductivity />
        </div>
        <div className={styles.chartCard}>
           <h3 className={styles.sectionTitle}>Time Logging</h3>
           <TimeReportTable workspaceId={workspaceId} />
        </div>
      </div>
    </div>
  );
};

export default WorkspaceAnalyticsTab;