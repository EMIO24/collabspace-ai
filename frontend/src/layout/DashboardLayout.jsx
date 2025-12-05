import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, Activity, Settings, MessageSquare, Puzzle, 
  PieChart, Search, Bell, Menu, ListTodo, Bot, FolderOpen,
  Briefcase, Plus, LogOut, User, LayoutGrid
} from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';
import Avatar from '../components/ui/Avatar/Avatar';
import GlobalSearch from '../features/search/GlobalSearch';
import ChatDrawer from '../features/ai/ChatDrawer';
import NotificationDropdown from '../components/ui/Notifications/NotificationDropdown';
import CreateTaskModal from '../features/kanban/CreateTaskModal';
import CreateProjectModal from '../features/projects/CreateProjectModal';
import CreateWorkspaceModal from '../features/workspaces/CreateWorkspaceModal';
import styles from './DashboardLayout.module.css';
import { api } from '../services/api';
import { toast } from 'react-hot-toast';

// --- Helper Component for Tooltip Logic ---
const NavItem = ({ to, icon: Icon, label, onHover, onLeave }) => {
  return (
    <NavLink 
      to={to}
      className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
      onMouseEnter={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        onHover(label, rect.top + (rect.height / 2)); // Pass label and center Y position
      }}
      onMouseLeave={onLeave}
    >
      <Icon size={24} />
      {/* We don't render the span inside here anymore to avoid clipping */}
    </NavLink>
  );
};

const Sidebar = () => {
  const { currentWorkspace } = useWorkspace();
  const [tooltip, setTooltip] = useState({ show: false, label: '', top: 0 });

  const handleHover = (label, top) => {
    setTooltip({ show: true, label, top });
  };

  const handleLeave = () => {
    setTooltip(prev => ({ ...prev, show: false }));
  };

  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <div className={styles.brandLogo}>C</div>
      </div>

      <nav className={styles.navScroll}>
        <NavItem to="/dashboard" icon={LayoutDashboard} label="Home" onHover={handleHover} onLeave={handleLeave} />
        <NavItem to="/tasks" icon={ListTodo} label="My Tasks" onHover={handleHover} onLeave={handleLeave} />
        <NavItem to="/meetings" icon={Bot} label="Meeting AI" onHover={handleHover} onLeave={handleLeave} />
        
        <div className={styles.divider} />

        <NavLink to="/workspaces" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
           onMouseEnter={(e) => handleHover('Workspaces', e.currentTarget.getBoundingClientRect().top + 28)}
           onMouseLeave={handleLeave}
        >
           <LayoutGrid size={24} />
        </NavLink>
        
        <NavItem to="/projects" icon={Activity} label="Projects" onHover={handleHover} onLeave={handleLeave} />
        <NavItem to="/files" icon={FolderOpen} label="Files" onHover={handleHover} onLeave={handleLeave} />
        <NavItem to="/chat" icon={MessageSquare} label="Messaging" onHover={handleHover} onLeave={handleLeave} />
        <NavItem to="/analytics" icon={PieChart} label="Analytics" onHover={handleHover} onLeave={handleLeave} />

        {currentWorkspace && (
          <NavItem 
             to={`/workspaces/${currentWorkspace.id}/settings`} 
             icon={Briefcase} 
             label="Team Settings" 
             onHover={handleHover} 
             onLeave={handleLeave} 
          />
        )}
        
        <div className={styles.divider} />

        <NavItem to="/marketplace" icon={Puzzle} label="Integrations" onHover={handleHover} onLeave={handleLeave} />
        <NavItem to="/settings/profile" icon={Settings} label="User Settings" onHover={handleHover} onLeave={handleLeave} />
      </nav>

      <div className={styles.userProfile}>
        <div className={styles.userCard}>
          <Avatar size="sm" fallback="U" />
        </div>
      </div>

      {/* Floating Tooltip Rendered Outside Scroll Container */}
      <div 
        className={`${styles.floatingTooltip} ${tooltip.show ? styles.tooltipVisible : ''}`}
        style={{ top: tooltip.top }}
      >
        {tooltip.label}
      </div>
    </aside>
  );
};

const Topbar = ({ onOpenModal }) => {
  const [showNotifs, setShowNotifs] = useState(false);
  const [showNewMenu, setShowNewMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    try { await api.post('/auth/logout/'); } catch (e) { console.error(e); }
    localStorage.removeItem('accessToken');
    navigate('/login');
    toast.success('Logged out successfully');
  };

  return (
    <header className={styles.topbar}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
         <span style={{ fontWeight: 800, fontSize: '1.4rem', color: '#1e293b', letterSpacing: '-0.03em' }}>
           CollabSpace <span style={{ color: '#7c3aed' }}>AI</span>
         </span>
      </div>

      <div className={styles.searchWrapper}>
        <Search size={18} className={styles.searchIcon} />
        <input 
          type="text" 
          placeholder="Search everything..." 
          className={styles.searchInput} 
          readOnly 
          onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
        />
        <span className={styles.searchKbd}>⌘K</span>
      </div>

      <div className={styles.actions}>
        {/* Quick Create */}
        <div style={{ position: 'relative' }}>
            <button className={styles.primaryBtn} onClick={() => setShowNewMenu(!showNewMenu)}>
                <Plus size={18} /> New
            </button>
            {showNewMenu && (
                <div className={styles.dropdownMenu} onMouseLeave={() => setShowNewMenu(false)}>
                    <button className={styles.dropdownItem} onClick={() => { onOpenModal('task'); setShowNewMenu(false); }}>
                        <ListTodo size={18} /> New Task
                    </button>
                    <button className={styles.dropdownItem} onClick={() => { onOpenModal('project'); setShowNewMenu(false); }}>
                        <Activity size={18} /> New Project
                    </button>
                    <button className={styles.dropdownItem} onClick={() => { onOpenModal('workspace'); setShowNewMenu(false); }}>
                        <Briefcase size={18} /> New Workspace
                    </button>
                </div>
            )}
        </div>

        {/* Notifications */}
        <div style={{ position: 'relative' }}>
          <button className={styles.iconBtn} onClick={() => setShowNotifs(!showNotifs)}>
            <Bell size={20} />
            <span className={styles.badge} />
          </button>
          {showNotifs && <NotificationDropdown onClose={() => setShowNotifs(false)} />}
        </div>

        {/* User Menu */}
        <div style={{ position: 'relative' }}>
            <div onClick={() => setShowUserMenu(!showUserMenu)} style={{ cursor: 'pointer' }}>
                <Avatar size="sm" fallback="U" />
            </div>
            {showUserMenu && (
                <div className={styles.dropdownMenu} onMouseLeave={() => setShowUserMenu(false)}>
                    <button className={styles.dropdownItem} onClick={() => navigate('/settings/profile')}>
                        <User size={16} /> Profile
                    </button>
                    <button className={styles.dropdownItem} onClick={() => navigate('/settings')}>
                        <Settings size={16} /> Settings
                    </button>
                    <div style={{ borderTop: '1px solid #f1f5f9', margin: '0.5rem 0' }} />
                    <button className={styles.dropdownItem} onClick={handleLogout} style={{ color: '#ef4444' }}>
                        <LogOut size={16} /> Sign Out
                    </button>
                </div>
            )}
        </div>
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
  const [activeModal, setActiveModal] = useState(null);

  return (
    <div className={styles.container}>
      <Sidebar />
      <div className={styles.mainContent}>
        <Topbar onOpenModal={setActiveModal} />
        <main className={styles.pageContent}>
          <Outlet />
        </main>
        <Footer />
      </div>
      
      <GlobalSearch />
      <ChatDrawer projectContextId={projectContextId} />

      {activeModal === 'task' && <CreateTaskModal projectId={null} onClose={() => setActiveModal(null)} />}
      {activeModal === 'project' && <CreateProjectModal onClose={() => setActiveModal(null)} />}
      {activeModal === 'workspace' && <CreateWorkspaceModal onClose={() => setActiveModal(null)} />}
    </div>
  );
};

export default DashboardLayout;