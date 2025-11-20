import React from 'react';
import PropTypes from 'prop-types';
import { NavLink } from 'react-router-dom';
import styles from './Sidebar.module.css';
import WorkspaceSelector from './WorkspaceSelector';
import { useSelector } from 'react-redux';

/**
 * Linear-style sidebar (icon-first). Controlled collapsed state is passed from AppLayout.
 * When collapsed: show icons only; expanded: show label tooltips and active indicator bar.
 */

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { to: '/projects', label: 'Projects', icon: 'folder' },
  { to: '/tasks', label: 'Tasks', icon: 'tasks' },
  { to: '/chat', label: 'Chat', icon: 'chat' },
  { to: '/calendar', label: 'Calendar', icon: 'calendar' },
  { to: '/documents', label: 'Documents', icon: 'documents' },
  { to: '/reports', label: 'Reports', icon: 'reports' },
  { to: '/settings', label: 'Settings', icon: 'settings' },
];

function Icon({ name, className }) {
  // small icon set - kept inline to avoid external deps
  switch (name) {
    case 'dashboard':
      return (
        <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="3" y="3" width="8" height="8" rx="1.5" />
          <rect x="13" y="3" width="8" height="5" rx="1.5" />
          <rect x="13" y="12" width="8" height="9" rx="1.5" />
          <rect x="3" y="13" width="8" height="7" rx="1.5" />
        </svg>
      );
    case 'folder':
      return (
        <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M3 7a2 2 0 0 1 2-2h3l2 2h7a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" />
        </svg>
      );
    case 'tasks':
      return (
        <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M9 11l2 2 4-4" />
          <path d="M21 12v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h4" />
        </svg>
      );
    case 'chat':
      return (
        <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      );
    case 'calendar':
      return (
        <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <path d="M16 3v4M8 3v4M3 11h18" />
        </svg>
      );
    case 'documents':
      return (
        <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <path d="M14 2v6h6" />
        </svg>
      );
    case 'reports':
      return (
        <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M3 3v18h18" />
          <path d="M8 13v-6M12 17V9M16 11v-4" />
        </svg>
      );
    case 'settings':
      return (
        <svg className={className} viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06A2 2 0 0 1 2.28 16.9l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82L4.25 3.72A2 2 0 0 1 7.08.89l.06.06c.5.5 1.22.57 1.82.33.8-.32 1.68-.32 2.48 0 .6.24 1.32.17 1.82-.33l.06-.06A2 2 0 0 1 19.72 3.1l-.06.06c-.5.5-.57 1.22-.33 1.82.32.8.32 1.68 0 2.48-.24.6-.17 1.32.33 1.82l.06.06A2 2 0 0 1 19.4 15z" />
        </svg>
      );
    default:
      return null;
  }
}

export default function Sidebar({ collapsed, onCloseMobile, isMobileOpen }) {
  const user = useSelector((s) => s.auth.user);
  return (
    <aside
      className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''} ${isMobileOpen ? styles.mobileOpen : ''}`}
      aria-hidden={isMobileOpen ? 'false' : 'true'}
    >
      <div className={styles.top}>
        <div className={styles.brand}>
          <div className={styles.logoMark}>CS</div>
          {!collapsed && <div className={styles.brandText}>CollabSpace</div>}
        </div>

        <div className={styles.workspaceWrap}>
          <WorkspaceSelector collapsed={collapsed} />
        </div>
      </div>

      <nav className={styles.nav} aria-label="Main navigation">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `${styles.item} ${isActive ? styles.active : ''}`
            }
            tabIndex={0}
            title={collapsed ? item.label : undefined}
            onClick={() => {
              if (isMobileOpen && onCloseMobile) onCloseMobile();
            }}
          >
            <div className={styles.iconWrap}>
              <Icon name={item.icon} className={styles.icon} />
              <span className={styles.activeBar} />
            </div>
            {!collapsed && <span className={styles.label}>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className={styles.bottom}>
        <div className={styles.userRow}>
          <img className={styles.avatar} src={user?.avatar || '/avatar-placeholder.png'} alt="avatar" />
          {!collapsed && <div className={styles.userName}>{user?.first_name || 'You'}</div>}
        </div>

        <button className={styles.collapseBtn} aria-label="Toggle sidebar" title="Toggle sidebar">
          {/* The toggle is handled by parent; style only */}
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M6 9l6 6 6-6" /></svg>
        </button>
      </div>

      {isMobileOpen && <div className={styles.mobileClose} onClick={onCloseMobile} aria-hidden="true" />}
    </aside>
  );
}

Sidebar.propTypes = {
  collapsed: PropTypes.bool,
  onCloseMobile: PropTypes.func,
  isMobileOpen: PropTypes.bool,
};
