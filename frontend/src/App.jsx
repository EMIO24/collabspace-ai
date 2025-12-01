import React, { useState } from 'react';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { api } from './services/api';
import DashboardLayout from './layouts/DashboardLayout';
import { Activity, Users, CheckCircle2, Settings } from 'lucide-react';

// ... (Keep your DashboardView and EmptyState components here or move to src/views/) ...

const AppContent = () => {
  const [activeRoute, setActiveRoute] = useState('dashboard');

  useQuery({
    queryKey: ['healthCheck'],
    queryFn: () => api.get('/core/health/'),
    retry: false
  });

  return (
    <DashboardLayout activeRoute={activeRoute} setActiveRoute={setActiveRoute}>
      {activeRoute === 'dashboard' && <DashboardView />}
      {activeRoute === 'team' && <EmptyState title="Team Management" />}
      {activeRoute === 'settings' && <EmptyState title="Global Settings" />}
    </DashboardLayout>
  );
};

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
