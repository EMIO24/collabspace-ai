import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { User, Shield, Bell, Puzzle } from 'lucide-react';
import styles from './SettingsLayout.module.css';

const SettingsLayout = () => {
  return (
    <div className={styles.container}>
      <nav className={styles.sidebar}>
        <NavLink 
          to="/settings/profile" 
          className={({ isActive }) => `${styles.navLink} ${isActive ? styles.activeLink : ''}`}
        >
          <User size={18} /> Profile
        </NavLink>
        <NavLink 
          to="/settings/security" 
          className={({ isActive }) => `${styles.navLink} ${isActive ? styles.activeLink : ''}`}
        >
          <Shield size={18} /> Security
        </NavLink>
        <NavLink 
          to="/settings/notifications" 
          className={({ isActive }) => `${styles.navLink} ${isActive ? styles.activeLink : ''}`}
        >
          <Bell size={18} /> Notifications
        </NavLink>
        <NavLink 
          to="/marketplace" 
          className={({ isActive }) => `${styles.navLink} ${isActive ? styles.activeLink : ''}`}
        >
          <Puzzle size={18} /> Integrations
        </NavLink>
      </nav>

      <div className={styles.content}>
        <Outlet />
      </div>
    </div>
  );
};

export default SettingsLayout;