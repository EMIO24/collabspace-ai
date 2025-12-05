import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

// ... (Keep all existing imports)
import { WorkspaceProvider } from './context/WorkspaceContext';
import AuthLayout from './layout/AuthLayout/AuthLayout';
import DashboardLayout from './layout/DashboardLayout';
import AuthGuard from './components/auth/AuthGuard';

// Auth Pages
import Login from './features/auth/Login';
import Register from './features/auth/Register';
import ForgotPassword from './features/auth/ForgotPassword';
import VerifyEmail from './features/auth/VerifyEmail';

// Core Pages
import ProfileDashboard from './features/profile/ProfileDashboard';
import WorkspacesPage from './pages/WorkspacesPage';
import ProjectsPage from './pages/ProjectsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import MessagingPage from './features/messaging/MessagingPage';
import IntegrationsPage from './pages/IntegrationsPage';

// Features
import MyTasksPage from './features/tasks/MyTasksPage';
import TaskCalendarPage from './pages/TaskCalendarPage'; // NEW IMPORT
import MeetingIntelligence from './features/ai/MeetingIntelligence';
import AIAnalyticsDashboard from './features/ai/AIAnalyticsDashboard';
import FileManager from './features/files/FileManager';
import SharedFileView from './features/files/SharedFileView';

// Sub-Pages
import ProjectLayout from './features/projects/ProjectLayout';
import ProjectOverview from './features/projects/ProjectOverview';
import ProjectCalendar from './features/projects/ProjectCalendar';
import KanbanBoard from './features/kanban/KanbanBoard';
import TaskListView from './features/tasks/TaskListView';
import ProjectFiles from './features/projects/ProjectFiles';
import ProjectTimelinePage from './pages/ProjectTimelinePage';
import ProjectSettings from './features/projects/ProjectSettings';
import WorkspaceDetail from './features/workspaces/WorkspaceDetail';
import WorkspaceSettings from './features/workspaces/settings/WorkspaceSettings';

// Settings
import SettingsLayout from './features/settings/SettingsLayout';
import ProfileSettings from './features/settings/ProfileSettings';
import SecuritySettings from './features/settings/SecuritySettings';
import NotificationSettings from './features/settings/NotificationSettings';
import WebhookSettings from './features/settings/WebhookSettings';
import AITemplateManager from './features/ai/AITemplateManager';
import TaskTemplates from './features/tasks/TaskTemplates';
import TeamProductivity from './features/analytics/TeamProductivity';

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

const StatusPage = () => <div style={{padding:'2rem', textAlign:'center'}}>System Operational</div>;
const NotFound = () => <div style={{padding:'2rem', textAlign:'center'}}>404 Not Found</div>;

const KanbanWrapper = () => {
  const { id } = useParams(); 
  return <KanbanBoard projectId={id} />;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Toaster position="top-right" />
      <Router>
        <Routes>
          {/* Public */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password/:uid/:token" element={<ForgotPassword />} />
            <Route path="/verify-email/:key" element={<VerifyEmail />} />
          </Route>
          <Route path="/status" element={<StatusPage />} />
          <Route path="/shared/:token" element={<SharedFileView />} />

          {/* Protected */}
          <Route path="/" element={<AuthGuard><WorkspaceProvider><DashboardLayout /></WorkspaceProvider></AuthGuard>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<ProfileDashboard />} />
            
            {/* Tasks & Calendar */}
            <Route path="tasks" element={<MyTasksPage />} />
            {/* ADDED: Global Task Calendar */}
            <Route path="calendar" element={<TaskCalendarPage />} /> 
            
            <Route path="meetings" element={<MeetingIntelligence />} />
            <Route path="files" element={<FileManager />} />
            <Route path="projects" element={<ProjectsPage />} />
            
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="analytics/ai" element={<AIAnalyticsDashboard />} />
            <Route path="analytics/team" element={<TeamProductivity />} />

            <Route path="chat" element={<MessagingPage />} />
            <Route path="marketplace" element={<IntegrationsPage />} />

            <Route path="projects/:id" element={<ProjectLayout />}>
              <Route index element={<ProjectOverview />} />
              <Route path="board" element={<KanbanWrapper />} />
              <Route path="list" element={<TaskListView />} />
              <Route path="calendar" element={<ProjectCalendar />} />
              <Route path="files" element={<ProjectFiles />} />
              <Route path="activity" element={<ProjectTimelinePage />} />
              <Route path="settings" element={<ProjectSettings />} />
            </Route>

            <Route path="workspaces" element={<WorkspacesPage />} />
            <Route path="workspaces/:id" element={<WorkspaceDetail />} />
            <Route path="workspaces/:id/settings" element={<WorkspaceSettings />} />

            <Route path="settings" element={<SettingsLayout />}>
              <Route index element={<Navigate to="profile" replace />} />
              <Route path="profile" element={<ProfileSettings />} />
              <Route path="security" element={<SecuritySettings />} />
              <Route path="notifications" element={<NotificationSettings />} />
              <Route path="webhooks" element={<WebhookSettings />} />
              <Route path="ai-templates" element={<AITemplateManager />} />
              <Route path="templates" element={<TaskTemplates />} />
            </Route>
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;