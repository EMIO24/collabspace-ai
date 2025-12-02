import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import Badge from '../../components/ui/Badge/Badge';
import TaskDetailSlideOver from './TaskDetailSlideOver';
import styles from './MyTasksPage.module.css';

const PRIORITY_COLORS = {
  low: 'info',
  medium: 'warning',
  high: 'danger'
};

const MyTasksPage = () => {
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [selectedTaskId, setSelectedTaskId] = useState(null);

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['myTasks', filterStatus, filterPriority],
    queryFn: async () => {
      // Build query string
      const params = new URLSearchParams({ assigned_to: 'me' });
      if (filterStatus) params.append('status', filterStatus);
      if (filterPriority) params.append('priority', filterPriority);
      
      const res = await api.get(`/tasks/tasks/?${params.toString()}`);
      return res.data;
    }
  });

  if (isLoading) return <div className="p-8 text-center">Loading your tasks...</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>My Tasks</h1>
        <div className={styles.controls}>
          <select 
            className={styles.select}
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>

          <select 
            className={styles.select}
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
          >
            <option value="">All Priorities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th style={{ width: '40%' }}>Task</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Due Date</th>
            </tr>
          </thead>
          <tbody>
            {tasks?.map(task => (
              <tr 
                key={task.id} 
                className={styles.row}
                onClick={() => setSelectedTaskId(task.id)}
                style={{ cursor: 'pointer' }}
              >
                <td>
                  <span className={styles.taskTitle}>{task.title}</span>
                  <span className={styles.projectName}>
                    {task.project_name || 'Unknown Project'}
                  </span>
                </td>
                <td>
                  <Badge variant="gray">{task.status.replace('_', ' ')}</Badge>
                </td>
                <td>
                  <Badge variant={PRIORITY_COLORS[task.priority] || 'gray'}>
                    {task.priority}
                  </Badge>
                </td>
                <td>
                  {task.due_date ? new Date(task.due_date).toLocaleDateString() : '-'}
                </td>
              </tr>
            ))}
            {!tasks?.length && (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
                  No tasks found matching your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <TaskDetailSlideOver 
        taskId={selectedTaskId} 
        onClose={() => setSelectedTaskId(null)} 
      />
    </div>
  );
};

export default MyTasksPage;