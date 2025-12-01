import React from 'react';
import { Calendar, ArrowRight } from 'lucide-react';
import styles from './ProjectCard.module.css';

const ProjectCard = ({ project, onClick }) => {
  // Generate a mock progress if none exists
  const progress = project.progress !== undefined ? project.progress : Math.floor(Math.random() * 80) + 10;

  return (
    <div className={styles.card} onClick={onClick}>
      <div className={styles.header}>
        <h3 className={styles.title}>{project.name}</h3>
        <span className={styles.statusBadge}>{project.status || 'Active'}</span>
      </div>

      <p className={styles.description}>
        {project.description || 'No description provided for this project.'}
      </p>

      <div className={styles.footer}>
        <div className={styles.progressContainer}>
          <div className={styles.progressHeader}>
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div className={styles.track}>
            <div className={styles.fill} style={{ width: `${progress}%` }} />
          </div>
        </div>

        <div className={styles.meta}>
          <Calendar size={14} className={styles.icon} />
          <span>
            {new Date(project.start_date).toLocaleDateString()} — {new Date(project.end_date).toLocaleDateString()}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ProjectCard;