import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts';
import { Download, Calendar, Activity, CheckCircle, Clock, Zap, AlertTriangle, Users } from 'lucide-react';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import styles from './AnalyticsDashboard.module.css';
import { toast } from 'react-hot-toast';

const COLORS = ['#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

const AnalyticsDashboard = () => {
  const { currentWorkspace } = useWorkspace();
  const workspaceId = currentWorkspace?.id;
  const [dateRange, setDateRange] = useState('30d');

  // --- DATA FETCHING ---
  const { data: metrics, isLoading, isError } = useQuery({
    queryKey: ['workspaceAnalytics', workspaceId, dateRange],
    queryFn: async () => {
      try {
         const res = await api.get(`/analytics/workspace/${workspaceId}/metrics/?range=${dateRange}`);
         return res.data;
      } catch (e) {
         console.error("Analytics API failed", e);
         throw e;
      }
    },
    enabled: !!workspaceId,
    retry: false 
  });

  // --- DATA NORMALIZATION ---
  
  // 1. Metrics Cards Data
  const stats = useMemo(() => ({
    completionRate: metrics?.tasks?.completion_rate || 0,
    avgTime: metrics?.tasks?.avg_completion_time_days || 0,
    totalHours: metrics?.time_tracking?.total_hours || 0,
    efficiency: metrics?.overview?.activity_rate || 0,
    totalProjects: metrics?.overview?.total_projects || 0
  }), [metrics]);

  // 2. Charts Data

  // Chart 1: Status Distribution (Donut)
  const statusData = useMemo(() => {
    if (!metrics?.distributions?.by_status) return [];
    return metrics.distributions.by_status.map(item => ({
      name: item.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value: item.count
    }));
  }, [metrics]);

  // Chart 2: Priority Breakdown (Bar)
  const priorityData = useMemo(() => {
    if (!metrics?.distributions?.by_priority) return [];
    return metrics.distributions.by_priority.map(item => ({
      name: item.priority.charAt(0).toUpperCase() + item.priority.slice(1),
      count: item.count
    }));
  }, [metrics]);

  // Chart 3: Task Completion Composition (Pie)
  const compositionData = useMemo(() => {
    if (!metrics?.tasks) return [];
    return [
      { name: 'Completed', value: metrics.tasks.completed },
      { name: 'Pending', value: metrics.tasks.pending }
    ].filter(i => i.value > 0);
  }, [metrics]);

  // Chart 4: Member Overview (Bar)
  // Since the endpoint provides aggregate member stats, we visualize Total vs Active
  const memberData = useMemo(() => {
    if (!metrics?.overview) return [];
    return [
      { name: 'Total Members', count: metrics.overview.total_members },
      { name: 'Active Members', count: metrics.overview.active_members }
    ];
  }, [metrics]);

  const handleExport = () => {
    toast.success('Report downloading...');
  };

  if (!workspaceId) return <div className={styles.loadingState}>Please select a workspace.</div>;
  if (isLoading) return <div className={styles.loadingState}>Loading analytics...</div>;

  if (isError) {
      return (
        <div className={styles.errorState}>
            <AlertTriangle size={48} className={styles.errorIcon} />
            <div>
                <h3 className={styles.errorTitle}>Analytics Unavailable</h3>
                <p>We couldn't fetch data for this workspace. Please try again later.</p>
            </div>
        </div>
      );
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.titleGroup}>
          <h1>Workspace Analytics</h1>
          <p className={styles.subtitle}>Performance insights for {currentWorkspace.name}</p>
        </div>
        <div className={styles.controls}>
          <div className={styles.dateControl}>
             <Calendar size={16} style={{ color: '#9ca3af' }} />
             <select 
               className={styles.dateSelect}
               value={dateRange}
               onChange={(e) => setDateRange(e.target.value)}
             >
               <option value="7d">Last 7 Days</option>
               <option value="30d">Last 30 Days</option>
               <option value="90d">Last Quarter</option>
             </select>
          </div>
          <button className={styles.exportBtn} onClick={handleExport}>
            <Download size={16} /> Export Report
          </button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className={styles.metricsGrid}>
        <MetricCard 
          label="Completion Rate" 
          value={`${stats.completionRate}%`} 
          icon={CheckCircle} 
          theme="green" 
        />
        <MetricCard 
          label="Avg Completion Time" 
          value={`${stats.avgTime.toFixed(1)} days`} 
          icon={Clock} 
          theme="blue" 
        />
        <MetricCard 
          label="Total Hours" 
          value={`${stats.totalHours.toFixed(1)}h`} 
          icon={Zap} 
          theme="purple" 
        />
        <MetricCard 
          label="Activity Rate" 
          value={`${stats.efficiency}%`} 
          icon={Activity} 
          theme="orange" 
        />
      </div>

      {/* Charts Grid */}
      <div className={styles.chartsGrid}>
        
        {/* 1. Task Status (Donut) */}
        <div className={styles.chartCard}>
           <div className={styles.chartHeader}>
             <h3 className={styles.chartTitle}>Task Status</h3>
           </div>
           <div className={styles.chartContainer}>
             {statusData.length > 0 ? (
                 <ResponsiveContainer width="100%" height="100%">
                   <PieChart>
                     <Pie
                       data={statusData}
                       cx="50%"
                       cy="50%"
                       innerRadius={60}
                       outerRadius={80}
                       paddingAngle={5}
                       dataKey="value"
                     >
                       {statusData.map((entry, index) => (
                         <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                       ))}
                     </Pie>
                     <Tooltip />
                     <Legend verticalAlign="bottom" height={36}/>
                   </PieChart>
                 </ResponsiveContainer>
             ) : (
                 <div className={styles.emptyChartState}>No status data available.</div>
             )}
           </div>
        </div>

        {/* 2. Priority Breakdown (Bar) */}
        <div className={styles.chartCard}>
           <div className={styles.chartHeader}>
             <h3 className={styles.chartTitle}>Task Priorities</h3>
           </div>
           <div className={styles.chartContainer}>
             {priorityData.length > 0 ? (
                 <ResponsiveContainer width="100%" height="100%">
                   <BarChart data={priorityData} layout="vertical" margin={{ left: 10 }}>
                     <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                     <XAxis type="number" hide />
                     <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} width={80} tick={{fontSize:12}} />
                     <Tooltip cursor={{fill: 'transparent'}} />
                     <Bar dataKey="count" name="Tasks" radius={[0, 4, 4, 0]} barSize={24}>
                        {priorityData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={['#ef4444', '#f59e0b', '#3b82f6'][index % 3] || '#8b5cf6'} />
                        ))}
                     </Bar>
                   </BarChart>
                 </ResponsiveContainer>
             ) : (
                 <div className={styles.emptyChartState}>No priority data available.</div>
             )}
           </div>
        </div>

        {/* 3. Workload Composition (Pie) */}
        <div className={styles.chartCard}>
           <div className={styles.chartHeader}>
             <h3 className={styles.chartTitle}>Workload Composition</h3>
           </div>
           <div className={styles.chartContainer}>
             {compositionData.length > 0 ? (
                 <ResponsiveContainer width="100%" height="100%">
                   <PieChart>
                     <Pie
                       data={compositionData}
                       cx="50%"
                       cy="50%"
                       outerRadius={80}
                       dataKey="value"
                       label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                     >
                       {compositionData.map((entry, index) => (
                         <Cell key={`cell-${index}`} fill={index === 0 ? '#10b981' : '#e2e8f0'} />
                       ))}
                     </Pie>
                     <Tooltip />
                   </PieChart>
                 </ResponsiveContainer>
             ) : (
                 <div className={styles.emptyChartState}>No tasks created yet.</div>
             )}
           </div>
        </div>

        {/* 4. Member Engagement (Bar) */}
        <div className={`${styles.chartCard} ${styles.fullWidth}`}>
           <div className={styles.chartHeader}>
             <h3 className={styles.chartTitle}>
               <Users size={20} className="text-blue-500 mr-2" /> Member Engagement
             </h3>
           </div>
           <div className={styles.chartContainer}>
             {memberData.length > 0 ? (
                 <ResponsiveContainer width="100%" height="100%">
                   <BarChart data={memberData} layout="vertical" margin={{ left: 20 }}>
                     <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                     <XAxis type="number" hide />
                     <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} width={100} />
                     <Tooltip cursor={{fill: 'rgba(0,0,0,0.02)'}} contentStyle={{borderRadius:'12px'}} />
                     <Legend />
                     <Bar dataKey="count" name="Users" fill="#6366f1" radius={[0, 4, 4, 0]} barSize={40} />
                   </BarChart>
                 </ResponsiveContainer>
             ) : (
                 <div className={styles.emptyChartState}>No member data available.</div>
             )}
           </div>
        </div>

      </div>
    </div>
  );
};

const MetricCard = ({ label, value, icon: Icon, theme }) => {
  const themeColors = {
    green: { bg: '#ecfdf5', text: '#10b981' },
    blue: { bg: '#eff6ff', text: '#3b82f6' },
    purple: { bg: '#f5f3ff', text: '#8b5cf6' },
    orange: { bg: '#fff7ed', text: '#f97316' }
  };
  const c = themeColors[theme] || themeColors.blue;

  return (
    <div className={styles.metricCard}>
      <div className={styles.metricHeader}>
        <span className={styles.metricLabel}>{label}</span>
        <div className={styles.iconBox} style={{ background: c.bg, color: c.text }}>
          <Icon size={20} />
        </div>
      </div>
      <div className={styles.metricValue}>{value}</div>
    </div>
  );
};

export default AnalyticsDashboard;