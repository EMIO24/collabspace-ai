import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import styles from './TimeReportTable.module.css';

const TimeReportTable = ({ workspaceId }) => {
  // Assuming endpoint for detailed time logs
  const { data: logs, isLoading } = useQuery({
    queryKey: ['timeReport', workspaceId],
    queryFn: async () => {
      const res = await api.get(`/analytics/workspace/${workspaceId}/time-report/`);
      return res.data;
    },
    enabled: !!workspaceId
  });

  if (isLoading) return <div>Loading Report...</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Team Time Logs</h3>
      </div>
      
      <div className={styles.tableContainer}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Team Member</th>
              <th>Task</th>
              <th>Date</th>
              <th>Duration</th>
            </tr>
          </thead>
          <tbody>
            {logs?.map((log) => (
              <tr key={log.id}>
                <td>
                  <div className={styles.userCell}>
                    <div className={styles.avatar}>
                      {log.user.username.charAt(0).toUpperCase()}
                    </div>
                    <span>{log.user.username}</span>
                  </div>
                </td>
                <td>{log.task_title}</td>
                <td>{new Date(log.date).toLocaleDateString()}</td>
                <td>
                  <span className="font-mono">{log.hours}h {log.minutes}m</span>
                </td>
              </tr>
            ))}
            {!logs?.length && (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>
                  No time logs recorded for this period.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TimeReportTable;