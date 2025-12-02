import React from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Activity, 
  Users, 
  Settings, 
  MessageSquare, 
  Puzzle, 
  PieChart, 
  Search, 
  Bell, 
  Menu 
} from 'lucide-react';
import WorkspaceSwitcher from '../features/workspaces/WorkspaceSwitcher';
import Avatar from '../components/ui/Avatar/Avatar';
import GlobalSearch from '../features/search/GlobalSearch';
import ChatDrawer from '../features/ai/ChatDrawer';
// Ensure GlobalSearch is imported if you want the Cmd+K modal available globally
import styles from './DashboardLayout.module.css';

const Sidebar = () => (
  <aside className={styles.sidebar}>
    <div className={styles.brand}>
      <div className={styles.brandLogo}>C</div>
      <span className={styles.brandName}>CollabSpace</span>
    </div>

    <div className="px-3 pt-4">
      <WorkspaceSwitcher />
    </div>

    <nav className={styles.nav}>
      <NavLink 
        to="/dashboard" 
        className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
      >
        <LayoutDashboard size={20} />
        Dashboard
      </NavLink>
      <NavLink 
        to="/projects" 
        className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
      >
        <Activity size={20} />
        Projects
      </NavLink>
      <NavLink 
        to="/chat" 
        className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
      >
        <MessageSquare size={20} />
        Messaging
      </NavLink>
      <NavLink 
        to="/analytics" 
        className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
      >
        <PieChart size={20} />
        Analytics
      </NavLink>
      <NavLink 
        to="/marketplace" 
        className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
      >
        <Puzzle size={20} />
        Integrations
      </NavLink>
      <div style={{ flex: 1 }} /> {/* Spacer */}
      <NavLink 
        to="/settings" 
        className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
      >
        <Settings size={20} />
        Settings
      </NavLink>
    </nav>

    <div className={styles.userProfile}>
      <div className={styles.userCard}>
        <Avatar size="sm" fallback="U" />
        <div className={styles.userInfo}>
          <div className={styles.userName}>Demo User</div>
          <div className={styles.userEmail}>user@collabspace.ai</div>
        </div>
      </div>
    </div>
  </aside>
);

const Topbar = () => (
  <header className={styles.topbar}>
    {/* Global Search Component handles the UI and Logic */}
    <div className={styles.searchWrapper}>
      <Search size={18} className={styles.searchIcon} />
      <input 
        type="text" 
        placeholder="Search (Cmd+K)..." 
        className={styles.searchInput} 
        readOnly // Let GlobalSearch handle the interaction via shortcuts
        onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
      />
    </div>

    <div className={styles.actions}>
      <button className={styles.iconBtn}>
        <Bell size={20} />
        <span className={styles.badge} />
      </button>
      <button className={`${styles.iconBtn} md:hidden`}>
        <Menu size={20} />
      </button>
    </div>
  </header>
);

const Footer = () => (
  <footer className={styles.footer}>
    <span>&copy; 2024 CollabSpace AI. All rights reserved.</span>
    <div className="flex gap-4">
      <span>Privacy Policy</span>
      <span>Terms of Service</span>
    </div>
  </footer>
);

const DashboardLayout = () => {
  // Use a random or fetched ID for the AI context
  const projectContextId = "global-context"; 

  return (
    <div className={styles.container}>
      <Sidebar />
      <div className={styles.mainContent}>
        <Topbar />
        <main className={styles.pageContent}>
          <Outlet />
        </main>
        <Footer />
      </div>
      
      {/* Global Overlays */}
      <GlobalSearch />
      <ChatDrawer projectContextId={projectContextId} />
    </div>
  );
};

export default DashboardLayout;