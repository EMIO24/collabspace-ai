import React, { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, Activity, Settings, MessageSquare, Puzzle, 
  PieChart, Search, Bell, Menu, ListTodo, Bot, FolderOpen
} from 'lucide-react';
import WorkspaceSwitcher from '../features/workspaces/WorkspaceSwitcher';
import Avatar from '../components/ui/Avatar/Avatar';
import GlobalSearch from '../features/search/GlobalSearch';
import ChatDrawer from '../features/ai/ChatDrawer';
import NotificationDropdown from '../components/ui/Notifications/NotificationDropdown';
import styles from './DashboardLayout.module.css';

const Sidebar = () => (
  <aside className={styles.sidebar}>
    <div className={styles.brand}>
      <div className={styles.brandLogo}>C</div>
      <span className={styles.brandName}>CollabSpace</span>
    </div>

    <div style={{ padding: '1rem 0.75rem 0' }}>
      <WorkspaceSwitcher />
    </div>

    <nav className={styles.navScroll}>
      <div className={styles.sectionHeader}>Overview</div>
      
      <NavLink to="/dashboard" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}>
        <LayoutDashboard size={20} /> Dashboard
      </NavLink>
      <NavLink to="/tasks" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}>
        <ListTodo size={20} /> My Tasks
      </NavLink>
      <NavLink to="/meetings" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}>
        <Bot size={20} /> Meeting AI
      </NavLink>

      <div className={styles.sectionHeader}>Workspace</div>
      
      <NavLink to="/projects" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}>
        <Activity size={20} /> Projects
      </NavLink>
      <NavLink to="/files" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}>
        <FolderOpen size={20} /> Files
      </NavLink>
      <NavLink to="/chat" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}>
        <MessageSquare size={20} /> Messaging
      </NavLink>
      <NavLink to="/analytics" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}>
        <PieChart size={20} /> Analytics
      </NavLink>

      <div className={styles.sectionHeader}>Configuration</div>

      <NavLink to="/marketplace" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}>
        <Puzzle size={20} /> Integrations
      </NavLink>
      <NavLink to="/settings/profile" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}>
        <Settings size={20} /> Settings
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

const Topbar = () => {
  const [showNotifs, setShowNotifs] = useState(false);

  return (
    <header className={styles.topbar}>
      <div className={styles.searchWrapper}>
        <Search size={18} className={styles.searchIcon} />
        <input 
          type="text" 
          placeholder="Search..." 
          className={styles.searchInput} 
        />
      </div>

      <div className={styles.actions}>
        <div style={{ position: 'relative' }}>
          <button 
            className={styles.iconBtn} 
            onClick={() => setShowNotifs(!showNotifs)}
          >
            <Bell size={20} />
            <span className={styles.badge} />
          </button>
          
          {showNotifs && (
            <NotificationDropdown onClose={() => setShowNotifs(false)} />
          )}
        </div>

        <button className={styles.iconBtn} style={{ display: 'none' }}>
          <Menu size={20} />
        </button>
      </div>
    </header>
  );
};

const Footer = () => (
  <footer className={styles.footer}>
    <span>&copy; 2024 CollabSpace AI. All rights reserved.</span>
    <div style={{ display: 'flex', gap: '1rem' }}>
      <span className={styles.link}>Privacy Policy</span>
      <span className={styles.link}>Terms of Service</span>
    </div>
  </footer>
);

const DashboardLayout = () => {
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
      
      <GlobalSearch />
      <ChatDrawer projectContextId={projectContextId} />
    </div>
  );
};

export default DashboardLayout;