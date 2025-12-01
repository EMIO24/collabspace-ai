import React from 'react';
import styles from './ProjectCard.module.css';

function ProjectCard({ project, viewMode = 'grid', onClick }) {
  const getStatusColor = (status) => {
    const colors = {
      planning: '#3b82f6',
      active: '#10b981',
      on_hold: '#f59e0b',
      completed: '#6b7280'
    };
    return colors[status] || '#6b7280';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      high: '#ef4444',
      medium: '#f59e0b',
      low: '#10b981'
    };
    return colors[priority] || '#6b7280';
  };

  const formatDate = (date) => {
    if (!date) return 'Not set';
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const calculateProgress = () => {
    if (!project.tasks || project.tasks.length === 0) return 0;
    const completed = project.tasks.filter(t => t.status === 'done').length;
    return Math.round((completed / project.tasks.length) * 100);
  };

  const progress = calculateProgress();

  return (
    <div
      className={`${styles.card} ${styles[viewMode]}`}
      onClick={onClick}
    >
      <div className={styles.header}>
        <h3 className={styles.title}>{project.name}</h3>
        <div className={styles.badges}>
          <span
            className={styles.badge}
            style={{ backgroundColor: getStatusColor(project.status) }}
          >
            {project.status?.replace('_', ' ')}
          </span>
          <span
            className={styles.badge}
            style={{ backgroundColor: getPriorityColor(project.priority) }}
          >
            {project.priority}
          </span>
        </div>
      </div>

      {project.description && (
        <p className={styles.description}>{project.description}</p>
      )}

      <div className={styles.progress}>
        <div className={styles.progressHeader}>
          <span className={styles.progressLabel}>Progress</span>
          <span className={styles.progressValue}>{progress}%</span>
        </div>
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className={styles.meta}>
        <div className={styles.metaItem}>
          <svg className={styles.icon} viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          <span>{formatDate(project.startDate)}</span>
        </div>
        {project.tasks && (
          <div className={styles.metaItem}>
            <svg className={styles.icon} viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M9 11l3 3L22 4" />
              <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
            </svg>
            <span>{project.tasks.filter(t => t.status === 'done').length}/{project.tasks.length} tasks</span>
          </div>
        )}
      </div>

      {project.team && project.team.length > 0 && (
        <div className={styles.team}>
          {project.team.slice(0, 3).map((member, index) => (
            <div
              key={member.id}
              className={styles.avatar}
              style={{ zIndex: 10 - index }}
              title={member.name}
            >
              {member.avatar ? (
                <img src={member.avatar} alt={member.name} />
              ) : (
                <span>{member.name.charAt(0).toUpperCase()}</span>
              )}
            </div>
          ))}
          {project.team.length > 3 && (
            <div className={styles.avatarMore}>
              +{project.team.length - 3}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ProjectCard;