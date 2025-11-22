import React, { useState, useEffect } from 'react';
import { getTasks } from '../../api/tasks';
import GanttChart from '../../components/project/GanttChart';
import styles from './ProjectTimelinePage.module.css';

function ProjectTimelinePage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('month'); // day, week, month
  const [filters, setFilters] = useState({
    status: 'all',
    priority: 'all',
  });

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const response = await getTasks();
      setTasks(response.data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredTasks = () => {
    let filtered = [...tasks];

    if (filters.status !== 'all') {
      filtered = filtered.filter(task => task.status === filters.status);
    }

    if (filters.priority !== 'all') {
      filtered = filtered.filter(task => task.priority === filters.priority);
    }

    return filtered;
  };

  const filteredTasks = getFilteredTasks();

  const taskStats = {
    total: filteredTasks.length,
    completed: filteredTasks.filter(t => t.status === 'done').length,
    inProgress: filteredTasks.filter(t => t.status === 'in_progress').length,
    upcoming: filteredTasks.filter(t => t.status === 'todo').length,
  };

  if (loading) {
    return <div className={styles.loading}>Loading timeline...</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Project Timeline</h1>
          <p className={styles.subtitle}>Gantt chart view of all tasks</p>
        </div>
        <div className={styles.viewModes}>
          <button
            className={`${styles.viewButton} ${viewMode === 'day' ? styles.active : ''}`}
            onClick={() => setViewMode('day')}
          >
            Day
          </button>
          <button
            className={`${styles.viewButton} ${viewMode === 'week' ? styles.active : ''}`}
            onClick={() => setViewMode('week')}
          >
            Week
          </button>
          <button
            className={`${styles.viewButton} ${viewMode === 'month' ? styles.active : ''}`}
            onClick={() => setViewMode('month')}
          >
            Month
          </button>
        </div>
      </div>

      <div className={styles.stats}>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Total Tasks</span>
          <span className={styles.statValue}>{taskStats.total}</span>
        </div>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Completed</span>
          <span className={`${styles.statValue} ${styles.completed}`}>{taskStats.completed}</span>
        </div>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>In Progress</span>
          <span className={`${styles.statValue} ${styles.inProgress}`}>{taskStats.inProgress}</span>
        </div>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Upcoming</span>
          <span className={`${styles.statValue} ${styles.upcoming}`}>{taskStats.upcoming}</span>
        </div>
      </div>

      <div className={styles.filters}>
        <div className={styles.filterGroup}>
          <label className={styles.filterLabel}>Status</label>
          <select
            className={styles.filterSelect}
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <option value="all">All Statuses</option>
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="review">Review</option>
            <option value="done">Done</option>
          </select>
        </div>
        <div className={styles.filterGroup}>
          <label className={styles.filterLabel}>Priority</label>
          <select
            className={styles.filterSelect}
            value={filters.priority}
            onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
          >
            <option value="all">All Priorities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      <div className={styles.chartContainer}>
        {filteredTasks.length === 0 ? (
          <div className={styles.empty}>No tasks to display</div>
        ) : (
          <GanttChart tasks={filteredTasks} viewMode={viewMode} />
        )}
      </div>

      <div className={styles.legend}>
        <div className={styles.legendItem}>
          <div className={`${styles.legendColor} ${styles.todoColor}`} />
          <span>To Do</span>
        </div>
        <div className={styles.legendItem}>
          <div className={`${styles.legendColor} ${styles.progressColor}`} />
          <span>In Progress</span>
        </div>
        <div className={styles.legendItem}>
          <div className={`${styles.legendColor} ${styles.reviewColor}`} />
          <span>Review</span>
        </div>
        <div className={styles.legendItem}>
          <div className={`${styles.legendColor} ${styles.doneColor}`} />
          <span>Done</span>
        </div>
      </div>
    </div>
  );
}

export default ProjectTimelinePage;