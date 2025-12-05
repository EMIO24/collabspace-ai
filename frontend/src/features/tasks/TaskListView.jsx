import React, { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import Avatar from '../../components/ui/Avatar/Avatar';
import Badge from '../../components/ui/Badge/Badge';
import { PRIORITY_MAP, STATUS_MAP } from '../../constants/enums'; 
import styles from './TaskListView.module.css';

const TaskListView = () => {
  const { id } = useParams();

  const { data: rawData, isLoading } = useQuery({
    queryKey: ['tasks', id],
    queryFn: async () => {
      const res = await api.get(`/tasks/tasks/?project=${id}`);
      return res.data;
    },
    enabled: !!id
  });

  // SAFETY CHECK: Normalize data
  const tasks = useMemo(() => {
    if (!rawData) return [];
    if (Array.isArray(rawData)) return rawData;
    if (rawData.results && Array.isArray(rawData.results)) return rawData.results;
    return [];
  }, [rawData]);

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading tasks...</div>;

  return (
    <div className={styles.container}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th className={styles.th}>Task Title</th>
            <th className={styles.th}>Status</th>
            <th className={styles.th}>Priority</th>
            <th className={styles.th}>Assignee</th>
            <th className={styles.th}>Due Date</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map(task => (
            <tr key={task.id} className={styles.tr}>
              <td className={styles.td}>
                <span className={styles.taskTitle}>{task.title}</span>
              </td>
              <td className={styles.td}>
                <Badge variant={STATUS_MAP?.[task.status]?.color || 'gray'}>
                  {STATUS_MAP?.[task.status]?.label || task.status}
                </Badge>
              </td>
              <td className={styles.td}>
                <Badge variant={PRIORITY_MAP?.[task.priority]?.color || 'gray'}>
                  {PRIORITY_MAP?.[task.priority]?.label || task.priority}
                </Badge>
              </td>
              <td className={styles.td}>
                {task.assigned_to ? (
                  <div className={styles.assignee}>
                    <Avatar 
                      src={task.assigned_to.avatar} 
                      fallback={task.assigned_to.username[0]} 
                      size="sm" 
                    />
                    <span>{task.assigned_to.username}</span>
                  </div>
                ) : (
                  <span className={styles.unassigned}>Unassigned</span>
                )}
              </td>
              <td className={styles.td}>
                {task.due_date ? new Date(task.due_date).toLocaleDateString() : '-'}
              </td>
            </tr>
          ))}
          {!tasks.length && (
            <tr>
              <td colSpan="5" className={styles.emptyState}>
                No tasks found in this project.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default TaskListView;