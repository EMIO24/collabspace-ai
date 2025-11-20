import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import styles from './AppLayout.module.css';
import Sidebar from './Sidebar';
import Header from './Header';
import Breadcrumbs from './Breadcrumbs';
import { useSelector, useDispatch } from 'react-redux';
import { setTheme } from '@store/slices/uiSlice';

/**
 * AppLayout composes Header + Sidebar + content. Controls collapsed state and mobile drawer.
 */
export default function AppLayout() {
  const ui = useSelector((s) => s.ui);
  const dispatch = useDispatch();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    // reflect global UI theme changes (example)
    dispatch(setTheme(ui.theme || 'light'));
  }, [ui.theme, dispatch]);

  function toggleSidebar() {
    setCollapsed((c) => !c);
  }

  return (
    <div className={styles.layout}>
      <Sidebar collapsed={collapsed} isMobileOpen={mobileOpen} onCloseMobile={() => setMobileOpen(false)} />

      <div className={`${styles.content} ${collapsed ? styles.contentShifted : ''}`}>
        <Header
          onMenuClick={() => setMobileOpen((v) => !v)}
          onSidebarToggle={toggleSidebar}
        />

        <main className={styles.main}>
          <div className={styles.container}>
            <Breadcrumbs />
            <Outlet />
          </div>
        </main>
      </div>

      {mobileOpen && <div className={styles.backdrop} onClick={() => setMobileOpen(false)} />}
    </div>
  );
}
