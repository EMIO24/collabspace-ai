import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, CheckCircle, Clock, Zap } from 'lucide-react';
import { api } from '../../services/api';
import styles from './WorkspaceMetrics.module.css';

const MetricCard = ({ label, value, trend, icon: Icon }) => (
  <div className={styles.card}>
    <div className={styles.label}>
      <Icon size={16} />
      {label}
    </div>
    <div className={styles.value}>{value}</div>
    {trend && (
      <div className={`${styles.trend} ${trend > 0 ? styles.positive : styles.negative}`}>
        {trend > 0 ? '+' : ''}{trend}% vs last month
      </div>
    )}
  </div>
);

const WorkspaceMetrics = ({ workspaceId }) => {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['workspaceMetrics', workspaceId],
    queryFn: async () => {
      const res = await api.get(`/analytics/workspace/${workspaceId}/metrics/?range=30d`);
      return res.data;
    },
    enabled: !!workspaceId
  });

  if (isLoading) {
    return <div className={styles.grid}>Loading Metrics...</div>;
  }

  return (
    <div className={styles.grid}>
      <MetricCard 
        label="Team Velocity" 
        value={`${metrics?.velocity || 0} pts`}
        trend={metrics?.velocity_trend}
        icon={Zap}
      />
      <MetricCard 
        label="Completion Rate" 
        value={`${metrics?.completion_rate || 0}%`}
        trend={metrics?.completion_trend}
        icon={CheckCircle}
      />
      <MetricCard 
        label="Total Hours" 
        value={`${metrics?.total_hours || 0}h`}
        trend={metrics?.hours_trend}
        icon={Clock}
      />
      <MetricCard 
        label="Active Tasks" 
        value={metrics?.active_tasks || 0}
        icon={Activity}
      />
    </div>
  );
};

export default WorkspaceMetrics;