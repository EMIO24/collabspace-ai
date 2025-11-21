import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getTasks } from '../../api/tasks'; // Placeholder API
import Widget from '../common/Widget';
import styles from './TasksSummaryWidget.module.css';

// Mock API for demonstration
const mockGetTasks = () => new Promise(resolve => {
    setTimeout(() => {
        resolve({
            data: [
                { id: 1, status: 'todo', due_date: '2025-11-25' },
                { id: 2, status: 'in_progress', due_date: '2025-11-20' }, // Overdue
                { id: 3, status: 'in_progress', due_date: '2025-12-01' },
                { id: 4, status: 'done', due_date: '2025-11-15' },
                { id: 5, status: 'todo', due_date: '2025-11-22' },
                { id: 6, status: 'todo', due_date: '2025-11-18' }, // Overdue
                { id: 7, status: 'todo', due_date: '2025-12-05' },
            ]
        });
    }, 1500); // Simulate network delay
});


export default function TasksSummaryWidget() {
  const [summary, setSummary] = useState({
    todo: 0,
    inProgress: 0,
    done: 0,
    overdue: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    loadSummary();
  }, []);
  
  const loadSummary = async () => {
    try {
      setError(null);
      // NOTE: Replace mockGetTasks with actual API call (e.g., getTasks)
      const response = await mockGetTasks(); 
      const tasks = response.data;
      const now = new Date();
      
      setSummary({
        todo: tasks.filter(t => t.status === 'todo').length,
        inProgress: tasks.filter(t => t.status === 'in_progress').length,
        done: tasks.filter(t => t.status === 'done').length,
        // Calculate overdue tasks that are not marked 'done'
        overdue: tasks.filter(t => new Date(t.due_date) < now && t.status !== 'done').length,
      });
    } catch (err) {
      console.error('Failed to load tasks summary:', err);
      setError('Failed to load task summary.');
    } finally {
      setLoading(false);
    }
  };
  
  // Loading State (Skeleton)
  if (loading) {
    return (
      <Widget title="My Tasks">
        <div className={styles.grid}>
          <div className={`${styles.statCard} ${styles.skeleton}`}></div>
          <div className={`${styles.statCard} ${styles.skeleton}`}></div>
          <div className={`${styles.statCard} ${styles.skeleton}`}></div>
          <div className={`${styles.statCard} ${styles.skeleton}`}></div>
        </div>
      </Widget>
    );
  }

  // Error State
  if (error) {
    return (
      <Widget title="My Tasks">
        <div className={styles.error}>{error}</div>
      </Widget>
    );
  }

  // Main Content
  return (
    <Widget title="My Tasks" action={<Link to="/tasks">View All</Link>}>
      <div className={styles.grid}>
        <div className={styles.statCard}>
          <div className={styles.statValue}>{summary.todo}</div>
          <div className={styles.statLabel}>To Do</div>
        </div>
        
        <div className={styles.statCard}>
          <div className={styles.statValue}>{summary.inProgress}</div>
          <div className={styles.statLabel}>In Progress</div>
        </div>
        
        <div className={styles.statCard}>
          <div className={styles.statValue}>{summary.done}</div>
          <div className={styles.statLabel}>Completed</div>
        </div>
        
        <div className={`${styles.statCard} ${styles.overdueCard}`}>
          <div className={styles.statValue}>{summary.overdue}</div>
          <div className={styles.statLabel}>Overdue</div>
        </div>
      </div>
    </Widget>
  );
}