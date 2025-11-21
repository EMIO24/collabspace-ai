import React from 'react';
import Widget from '../common/Widget';
import styles from './AnalyticsWidget.module.css';

// Placeholder for a chart component (e.g., recharts, chart.js)
const MockChart = () => (
  <div className={styles.mockChart}>
    <p>Placeholder for Time Spent/Burnup Chart</p>
  </div>
);

export default function AnalyticsWidget() {
  const loading = false;
  const error = null;

  if (loading) {
    return (
      <Widget title="Performance Metrics">
        <div className={styles.loading}>Loading metrics...</div>
      </Widget>
    );
  }

  if (error) {
    return (
      <Widget title="Performance Metrics">
        <div className={styles.error}>{error}</div>
      </Widget>
    );
  }

  return (
    <Widget title="Performance Metrics" className={styles.analyticsWidget}>
      <MockChart />
      <div className={styles.summaryStats}>
        <div className={styles.stat}>
          <span className={styles.value}>45h</span>
          <span className={styles.label}>Time Logged This Week</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.value}>92%</span>
          <span className={styles.label}>Completion Rate</span>
        </div>
      </div>
    </Widget>
  );
}