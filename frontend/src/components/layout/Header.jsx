import React from 'react';
import PropTypes from 'prop-types';
import styles from './Header.module.css';
import SearchBar from './SearchBar';
import UserDropdown from './UserDropdown';
import NotificationDropdown from './NotificationDropdown';
import { useDispatch, useSelector } from 'react-redux';
import { toggleSidebar as toggleSidebarAction } from '@store/slices/uiSlice';

/**
 * Header with small controls. Parent (AppLayout) passes toggles for mobile menu.
 */
export default function Header({ onMenuClick, onSidebarToggle }) {
  const dispatch = useDispatch();
  const sidebarOpen = useSelector((s) => s.ui.sidebarOpen);

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <button className={styles.iconBtn} onClick={onMenuClick} aria-label="Open menu">
          {/* hamburger */}
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
        </button>

        <button
          className={styles.iconBtn}
          onClick={() => {
            // notify global UI slice
            dispatch(toggleSidebarAction());
            if (onSidebarToggle) onSidebarToggle();
          }}
          aria-label="Toggle sidebar"
          title="Toggle sidebar"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M6 4v16M18 4v16" /></svg>
        </button>

        <div className={styles.separator} />
        <SearchBar />
      </div>

      <div className={styles.right}>
        <NotificationDropdown />
        <UserDropdown />
      </div>
    </header>
  );
}

Header.propTypes = {
  onMenuClick: PropTypes.func,
  onSidebarToggle: PropTypes.func,
};
