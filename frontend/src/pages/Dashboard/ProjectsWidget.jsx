import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import Widget from '../common/Widget';
import styles from './ProjectsWidget.module.css';

const mockProjects = [
  { id: 1, name: 'Marketing Relaunch', progress: 75, status: 'Active' },
  { id: 2, name: 'CollabSpace AI Backend', progress: 40, status: 'In Progress' },
  { id: 3, name: 'Q4 Budget Review', progress: 100, status: 'Completed' },
];

export default function ProjectsWidget() {
  const [projects, setProjects] = useState(mockProjects);
  const [loading] = useState(false);
  const [error] = useState(null);

  if (loading) {
    return (
      <Widget title="My Projects">
        <div className={styles.loading}>Loading projects...</div>
      </Widget>
    );
  }

  if (error) {
    return (
      <Widget title="My Projects">
        <div className={styles.error}>{error}</div>
      </Widget>
    );
  }

  if (projects.length === 0) {
    return (
      <Widget title="My Projects" action={<Link to="/projects/new">Create New</Link>}>
        <div className={styles.empty}>You are not currently assigned to any projects.</div>
      </Widget>
    );
  }

  return (
    <Widget title="My Projects" action={<Link to="/projects">View All</Link>}>
      <ul className={styles.projectList}>
        {projects.map(p => (
          <li key={p.id} className={styles.projectItem}>
            <Link to={`/projects/${p.id}`} className={styles.projectName}>{p.name}</Link>
            <div className={styles.progressContainer}>
              <div 
                className={styles.progressBar} 
                style={{ width: `${p.progress}%` }} 
                data-progress={`${p.progress}%`}
              ></div>
            </div>
            <span className={styles.status}>{p.status}</span>
          </li>
        ))}
      </ul>
    </Widget>
  );
}