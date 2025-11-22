import React, { useState, useEffect } from 'react';
import styles from './ProjectFilters.module.css';

function ProjectFilters({ onFilterChange }) {
  const [filters, setFilters] = useState({
    search: '',
    status: 'all',
    priority: 'all',
    sortBy: 'date',
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
      sortBy: 'date',
    });
  };

  const hasActiveFilters = filters.search || filters.status !== 'all' || filters.priority !== 'all' || filters.sortBy !== 'date';

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
          placeholder="Search projects..."
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
            <option value="planning">Planning</option>
            <option value="active">Active</option>
            <option value="on_hold">On Hold</option>
            <option value="completed">Completed</option>
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
          <label className={styles.label}>Sort By</label>
          <select
            className={styles.select}
            value={filters.sortBy}
            onChange={(e) => handleChange('sortBy', e.target.value)}
          >
            <option value="date">Date Created</option>
            <option value="name">Name</option>
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

export default ProjectFilters;