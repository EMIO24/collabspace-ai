import React from 'react';
import TasksSummaryWidget from '../../components/Dashboard/TasksSummaryWidget';
import ProjectsWidget from '../../components/Dashboard/ProjectsWidget';
import AnalyticsWidget from '../../components/Dashboard/AnalyticsWidget';
import ActivityFeedWidget from '../../components/Dashboard/ActivityFeedWidget';
import UpcomingWidget from '../../components/Dashboard/UpcomingWidget';
import TeamMembersWidget from '../../components/Dashboard/TeamMembersWidget';
import styles from './DashboardPage.module.css';

export default function DashboardPage() {
  const user = { firstName: 'Alex' }; // Mock user context

  return (
    <div className={styles.dashboard}>
      <header className={styles.header}>
        <h1 className={styles.greeting}>Welcome back, {user.firstName}!</h1>
        <p className={styles.tagline}>A summary of your projects and tasks.</p>
      </header>

      <section className={styles.mainGrid}>
        {/* Row 1: Key Metrics and Primary Widgets */}
        <div className={styles.tasksSummary}>
          <TasksSummaryWidget />
        </div>
        
        <div className={styles.projectsWidget}>
          <ProjectsWidget />
        </div>

        {/* Row 2: Analytics & Activity */}
        <div className={styles.analyticsWidget}>
          <AnalyticsWidget />
        </div>

        <div className={styles.activityFeedWidget}>
          <ActivityFeedWidget />
        </div>
        
        {/* Row 3: Utility/Secondary Widgets */}
        <div className={styles.upcomingWidget}>
          <UpcomingWidget />
        </div>

        <div className={styles.teamMembersWidget}>
          <TeamMembersWidget />
        </div>
      </section>
    </div>
  );
}