import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'framer-motion';
import { 
  Activity, LayoutDashboard, Settings, Users, Bell, 
  Search, LogOut, Server 
} from 'lucide-react';
import clsx from 'clsx';
import { api, NetworkEvents } from '../services/api';

// --- Sub-components (Sidebar, Topbar, etc.) ---
// You can extract these into separate files like components/Sidebar.jsx later

const MaintenanceModal = ({ isActive }) => (
  <AnimatePresence>
    {isActive && (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[9999] flex items-center justify-center bg-gray-900/80 backdrop-blur-md"
      >
        <motion.div 
          initial={{ scale: 0.9, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          className="bg-white p-8 rounded-2xl max-w-md text-center shadow-2xl"
        >
          <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-6">
            <Server size={32} />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">System Under Maintenance</h2>
          <p className="text-gray-600 mb-6">
            CollabSpace AI is currently undergoing scheduled maintenance. 
            We will be back shortly.
          </p>
          <button 
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Retry Connection
          </button>
        </motion.div>
      </motion.div>
    )}
  </AnimatePresence>
);

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
  <div 
    onClick={onClick}
    className={clsx(
      "flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all duration-200 group mb-1",
      active 
        ? "bg-indigo-50 text-indigo-700 font-medium shadow-sm" 
        : "text-gray-500 hover:bg-white/50 hover:text-gray-900"
    )}
  >
    <Icon size={20} className={clsx(active ? "text-indigo-600" : "text-gray-400 group-hover:text-gray-600")} />
    <span>{label}</span>
    {active && (
      <motion.div 
        layoutId="active-indicator"
        className="ml-auto w-1.5 h-1.5 rounded-full bg-indigo-600" 
      />
    )}
  </div>
);

const Sidebar = ({ currentRoute, setRoute }) => (
  <aside className="fixed left-0 top-0 bottom-0 w-64 glass-panel z-40 flex flex-col m-4 rounded-2xl border-opacity-50">
    <div className="h-20 flex items-center px-6 border-b border-gray-100/50">
      <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center mr-3 shadow-lg shadow-indigo-200">
        <Activity className="text-white" size={18} />
      </div>
      <span className="font-bold text-lg tracking-tight text-gray-800">CollabSpace AI</span>
    </div>

    <nav className="flex-1 px-3 py-6 overflow-y-auto">
      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-4 mb-4">Platform</div>
      <SidebarItem 
        icon={LayoutDashboard} 
        label="Dashboard" 
        active={currentRoute === 'dashboard'} 
        onClick={() => setRoute('dashboard')}
      />
      <SidebarItem 
        icon={Users} 
        label="Team" 
        active={currentRoute === 'team'} 
        onClick={() => setRoute('team')}
      />
      <SidebarItem 
        icon={Settings} 
        label="Settings" 
        active={currentRoute === 'settings'} 
        onClick={() => setRoute('settings')}
      />
    </nav>

    <div className="p-4 border-t border-gray-100/50">
      <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/40 transition-colors cursor-pointer">
        <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-400 to-purple-400 flex items-center justify-center text-white font-medium text-sm">
          JD
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">Jane Doe</p>
          <p className="text-xs text-gray-500 truncate">Senior Engineer</p>
        </div>
        <LogOut size={16} className="text-gray-400" />
      </div>
    </div>
  </aside>
);

const Topbar = () => (
  <header className="sticky top-0 z-30 h-20 px-8 flex items-center justify-between">
    <div>
      <h1 className="text-2xl font-bold text-gray-800">Overview</h1>
      <p className="text-sm text-gray-500">Welcome back, here's what's happening today.</p>
    </div>
    <div className="flex items-center gap-4">
      <div className="relative hidden md:block group">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-hover:text-indigo-500 transition-colors" size={18} />
        <input 
          type="text" 
          placeholder="Search projects..." 
          className="pl-10 pr-4 py-2.5 rounded-xl bg-white/50 border border-transparent focus:bg-white focus:border-indigo-200 focus:ring-4 focus:ring-indigo-100 outline-none transition-all w-64 text-sm"
        />
      </div>
      <div className="h-8 w-px bg-gray-300/50 mx-2"></div>
      <button className="btn-icon relative">
        <Bell size={20} />
        <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-gray-100"></span>
      </button>
    </div>
  </header>
);

const Footer = () => {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: () => api.get('/core/status/').then(res => res.data),
    refetchInterval: 30000,
  });

  return (
    <footer className="mt-auto py-6 px-8 border-t border-gray-200/50">
      <div className="flex flex-col md:flex-row justify-between items-center text-xs text-gray-500 gap-4">
        <div className="flex items-center gap-6">
          <span>&copy; 2025 CollabSpace AI Inc.</span>
          <a href="#" className="hover:text-indigo-600 transition-colors">Privacy</a>
          <a href="#" className="hover:text-indigo-600 transition-colors">Terms</a>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-white/40 rounded-full border border-white/60 shadow-sm">
          {isLoading ? (
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
          ) : isError ? (
            <div className="w-2 h-2 bg-red-500 rounded-full" />
          ) : (
            <div className="w-2 h-2 bg-emerald-500 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.4)]" />
          )}
          <span className="font-medium">
            {isLoading ? 'Checking Systems...' : isError ? 'Status Unknown' : `System: ${data.system} (${data.latency})`}
          </span>
        </div>
      </div>
    </footer>
  );
};

export default function DashboardLayout({ children, activeRoute, setActiveRoute }) {
  const [maintenanceMode, setMaintenanceMode] = useState(false);

  useEffect(() => {
    const handleMaintenance = () => setMaintenanceMode(true);
    const handleUnauthorized = () => alert("Session expired. Redirecting...");

    NetworkEvents.on('MAINTENANCE_MODE', handleMaintenance);
    NetworkEvents.on('UNAUTHORIZED', handleUnauthorized);
  }, []);

  return (
    <div className="flex min-h-screen">
      <MaintenanceModal isActive={maintenanceMode} />
      <div className="w-72 flex-shrink-0 hidden md:block">
        <Sidebar currentRoute={activeRoute} setRoute={setActiveRoute} />
      </div>
      <main className="flex-1 flex flex-col min-w-0 pl-4 md:pl-0">
        <Topbar />
        <div className="p-8 pt-4 flex-1">
          {children}
        </div>
        <Footer />
      </main>
    </div>
  );
}