import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import styles from './ProjectActivity.module.css';

const ProjectActivity = ({ projectId }) => {
  const { data: activities, isLoading } = useQuery({
    queryKey: ['projectActivity', projectId],
    queryFn: async () => {
      const res = await api.get(`/projects/${projectId}/activity/`);
      return res.data;
    },
    enabled: !!projectId
  });

  if (isLoading) return <div className="p-4 text-gray-400 text-sm">Loading timeline...</div>;
  if (!activities || activities.length === 0) return <div className="p-4 text-gray-400 text-sm">No recent activity.</div>;

  return (
    <div className={styles.container}>
      <h4 className={styles.header}>Project Activity</h4>
      <div className={styles.timeline}>
        {activities.map((log) => (
          <div key={log.id} className={styles.item}>
            <div className={styles.dot} />
            <div className={styles.card}>
              <span className={styles.timestamp}>
                {new Date(log.created_at || Date.now()).toLocaleString()}
              </span>
              <p className={styles.message}>{log.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProjectActivity;