import React from 'react';
import { Outlet, NavLink, useParams } from 'react-router-dom';
import { 
  LayoutTemplate, 
  KanbanSquare, 
  ListTodo, 
  FolderOpen, 
  History, 
  Settings,
  Calendar
} from 'lucide-react';
import styles from './ProjectLayout.module.css';

const ProjectLayout = () => {
  const { id } = useParams();

  return (
    <div className={styles.container}>
      {/* Secondary Project Navigation */}
      <div className={styles.topNav}>
        <NavLink 
          to={`/projects/${id}`} 
          end
          className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ''}`}
        >
          <LayoutTemplate size={16} /> Overview
        </NavLink>
        
        <NavLink 
          to={`/projects/${id}/board`} 
          className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ''}`}
        >
          <KanbanSquare size={16} /> Board
        </NavLink>

        <NavLink 
          to={`/projects/${id}/list`} 
          className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ''}`}
        >
          <ListTodo size={16} /> List
        </NavLink>

        <NavLink 
          to={`/projects/${id}/calendar`} 
          className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ''}`}
        >
          <Calendar size={16} /> Calendar
        </NavLink>

        <NavLink 
          to={`/projects/${id}/files`} 
          className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ''}`}
        >
          <FolderOpen size={16} /> Files
        </NavLink>

        <NavLink 
          to={`/projects/${id}/activity`} 
          className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ''}`}
        >
          <History size={16} /> Activity
        </NavLink>

        <div style={{ flex: 1 }} />

        <NavLink 
          to={`/projects/${id}/settings`} 
          className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ''}`}
        >
          <Settings size={16} /> Settings
        </NavLink>
      </div>

      <div className={styles.content}>
        <Outlet />
      </div>
    </div>
  );
};

export default ProjectLayout;