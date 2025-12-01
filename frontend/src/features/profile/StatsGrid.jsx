import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { CheckCircle2, FolderPlus, TrendingUp } from 'lucide-react';
import { api } from '../../services/api'; // Assumes api instance from Prompt 1
import Card from '../../components/ui/Card/Card';

const StatCard = ({ label, value, icon: Icon, colorClass }) => (
  <Card className="p-6 flex flex-col items-center justify-center gap-4 hover:bg-white/40 transition-colors">
    <div className={`p-3 rounded-full ${colorClass} bg-opacity-20`}>
      <Icon size={32} className={colorClass.replace('bg-', 'text-')} />
    </div>
    <div className="text-center">
      <h3 className="text-3xl font-bold text-gray-800">{value}</h3>
      <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">{label}</p>
    </div>
  </Card>
);

const StatsGrid = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['userStats'],
    queryFn: async () => {
      const res = await api.get('/auth/stats/');
      return res.data;
    }
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse">
        {[1, 2, 3].map(i => <div key={i} className="h-40 bg-white/30 rounded-2xl" />)}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <StatCard 
        label="Tasks Completed" 
        value={stats?.tasks_completed || 0} 
        icon={CheckCircle2} 
        colorClass="bg-emerald-500 text-emerald-600" 
      />
      <StatCard 
        label="Projects Created" 
        value={stats?.projects_created || 0} 
        icon={FolderPlus} 
        colorClass="bg-blue-500 text-blue-600" 
      />
      <StatCard 
        label="Productivity Score" 
        value={`${stats?.productivity_score || 0}%`} 
        icon={TrendingUp} 
        colorClass="bg-purple-500 text-purple-600" 
      />
    </div>
  );
};

export default StatsGrid;