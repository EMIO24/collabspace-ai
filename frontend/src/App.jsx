import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

// Contexts
import { WorkspaceProvider } from './context/WorkspaceContext';

// Layouts - CORRECTED IMPORTS
import AuthLayout from './layout/AuthLayout/AuthLayout';
import DashboardLayout from './layout/DashboardLayout';

// Guards
import AuthGuard from './components/auth/AuthGuard';

// Pages - Auth
import Login from './features/auth/Login';
import Register from './features/auth/Register';
import ForgotPassword from './features/auth/ForgotPassword';
import VerifyEmail from './features/auth/VerifyEmail';

// Pages - Dashboard
import ProfileDashboard from './features/profile/ProfileDashboard';
import ProjectsPage from './pages/ProjectsPage';
import MessagingPage from './features/messaging/MessagingPage';
import IntegrationsPage from './pages/IntegrationsPage';
import AnalyticsPage from './pages/AnalyticsPage';

// Global Styles
import './styles/variables.css';
import './index.css'; 

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
});

// System Status Page (Public)
const StatusPage = () => (
  <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-main)' }}>
    <h1>System Status: Operational</h1>
    <p>All systems go.</p>
  </div>
);

// 404 Page
const NotFound = () => (
  <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
    <h1 style={{ fontSize: '4rem', fontWeight: 'bold', color: 'var(--primary)' }}>404</h1>
    <p style={{ color: 'var(--text-muted)' }}>Page not found</p>
  </div>
);

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Toaster position="top-right" />
      
      <Router>
        <Routes>
          {/* --- PUBLIC ROUTES --- */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password/:uid/:token" element={<ForgotPassword />} />
            <Route path="/verify-email/:key" element={<VerifyEmail />} />
          </Route>

          <Route path="/status" element={<StatusPage />} />
          
          {/* --- PROTECTED ROUTES --- */}
          <Route 
            path="/" 
            element={
              <AuthGuard>
                <WorkspaceProvider>
                  <DashboardLayout />
                </WorkspaceProvider>
              </AuthGuard>
            }
          >
            {/* Redirect root to dashboard */}
            <Route index element={<Navigate to="/dashboard" replace />} />
            
            <Route path="dashboard" element={<ProfileDashboard />} />
            
            <Route path="projects">
              <Route index element={<ProjectsPage />} />
              <Route path=":id" element={<div>Project Details Placeholder</div>} />
            </Route>

            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="chat" element={<MessagingPage />} />
            <Route path="marketplace" element={<IntegrationsPage />} />
            <Route path="settings" element={<div>Settings Placeholder</div>} />
          </Route>

          {/* Catch All */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;