import React from 'react';
import { Link } from 'react-router-dom';
import styles from './Header.module.css';
import Logo from '@components/common/Logo/Logo';

export default function Header() {
  return (
    <header className={styles.header}>
      <div className="container" style={{display: 'flex', alignItems:'center', justifyContent:'space-between'}}>
        <div style={{display:'flex', alignItems:'center'}}>
          <Logo />
          <nav className={styles.nav}>
            <Link to="/dashboard">Dashboard</Link>
            <Link to="/workspaces">Workspaces</Link>
            <Link to="/projects">Projects</Link>
          </nav>
        </div>
        <div className={styles.right}>
          <Link to="/settings">Settings</Link>
        </div>
      </div>
    </header>
  );
}
