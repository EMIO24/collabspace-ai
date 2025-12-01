import React, { useState, useEffect } from 'react';
import styles from './TaskFilters.module.css';

function TaskFilters({ onFilterChange }) {
  const [filters, setFilters] = useState({
    search: '',
    status: 'all',
    priority: 'all',
    assignee: 'all',
    sortBy: 'created',
  });

  useEffect(() => {
    onFilterChange(filters);
  }, [filters, onFilterChange]);

  const handleChange = (name, value) => {
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleReset = () => {
    setFilters({
      search: '',
      status: 'all',
      priority: 'all',
      assignee: 'all',
      sortBy: 'created',
    });
  };

  const hasActiveFilters = 
    filters.search || 
    filters.status !== 'all' || 
    filters.priority !== 'all' || 
    filters.assignee !== 'all' || 
    filters.sortBy !== 'created';

  return (
    <div className={styles.container}>
      <div className={styles.searchContainer}>
        <svg className={styles.searchIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
        <input
          type="text"
          className={styles.searchInput}
          placeholder="Search tasks..."
          value={filters.search}
          onChange={(e) => handleChange('search', e.target.value)}
        />
      </div>

      <div className={styles.filters}>
        <div className={styles.filterGroup}>
          <label className={styles.label}>Status</label>
          <select
            className={styles.select}
            value={filters.status}
            onChange={(e) => handleChange('status', e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="review">Review</option>
            <option value="done">Done</option>
          </select>
        </div>

        <div className={styles.filterGroup}>
          <label className={styles.label}>Priority</label>
          <select
            className={styles.select}
            value={filters.priority}
            onChange={(e) => handleChange('priority', e.target.value)}
          >
            <option value="all">All Priorities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        <div className={styles.filterGroup}>
          <label className={styles.label}>Assignee</label>
          <select
            className={styles.select}
            value={filters.assignee}
            onChange={(e) => handleChange('assignee', e.target.value)}
          >
            <option value="all">All Assignees</option>
            <option value="1">John Doe</option>
            <option value="2">Jane Smith</option>
            <option value="unassigned">Unassigned</option>
          </select>
        </div>

        <div className={styles.filterGroup}>
          <label className={styles.label}>Sort By</label>
          <select
            className={styles.select}
            value={filters.sortBy}
            onChange={(e) => handleChange('sortBy', e.target.value)}
          >
            <option value="created">Date Created</option>
            <option value="title">Title</option>
            <option value="dueDate">Due Date</option>
            <option value="priority">Priority</option>
          </select>
        </div>

        {hasActiveFilters && (
          <button className={styles.resetButton} onClick={handleReset}>
            Reset Filters
          </button>
        )}
      </div>
    </div>
  );
}

export default TaskFilters;