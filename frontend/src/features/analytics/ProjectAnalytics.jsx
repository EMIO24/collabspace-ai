import React, { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import { Activity, Calendar, TrendingUp, Clock, Users, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';
import styles from './ProjectAnalytics.module.css';

const COLORS = ['#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];
const PRIORITY_COLORS = {
  low: '#3b82f6',
  medium: '#f59e0b',
  high: '#ef4444',
  urgent: '#7c3aed'
};

const ProjectAnalytics = () => {
  const { id } = useParams();
  const [timeRange, setTimeRange] = useState('all');

  // 1. Fetch Project Details
  const { data: project, isLoading: loadingProject } = useQuery({
    queryKey: ['project', id],
    queryFn: async () => {
      const res = await api.get(`/projects/${id}/`);
      return res.data;
    },
    enabled: !!id
  });

  // 2. Fetch All Tasks
  const { data: rawTasks, isLoading: loadingTasks } = useQuery({
    queryKey: ['projectTasks', id],
    queryFn: async () => {
      const res = await api.get(`/tasks/tasks/?project=${id}`);
      return res.data;
    },
    enabled: !!id
  });

  // --- DATA PROCESSING ---
  const tasks = useMemo(() => {
    if (!rawTasks) return [];
    if (Array.isArray(rawTasks)) return rawTasks;
    return rawTasks.results || [];
  }, [rawTasks]);

  const stats = project?.statistics || {
    total_tasks: 0,
    completed_tasks: 0,
    progress_percentage: 0,
    total_members: 0,
    days_active: 0
  };

  // Chart 1: Status Distribution
  const statusData = useMemo(() => {
    const counts = { todo: 0, in_progress: 0, review: 0, done: 0 };
    tasks.forEach(t => {
      const s = t.status || 'todo';
      const key = s === 'completed' ? 'done' : s;
      if (counts[key] !== undefined) counts[key]++;
    });

    return Object.keys(counts).map(key => ({
      name: key.replace('_', ' ').toUpperCase(),
      value: counts[key]
    })).filter(d => d.value > 0);
  }, [tasks]);

  // Chart 2: Member Workload
  const memberData = useMemo(() => {
    const map = {};
    tasks.forEach(t => {
      const name = t.assigned_to?.username || 'Unassigned';
      if (!map[name]) map[name] = { name, tasks: 0, completed: 0 };
      map[name].tasks++;
      if (t.status === 'done' || t.status === 'completed') map[name].completed++;
    });
    return Object.values(map);
  }, [tasks]);

  // Chart 3: Creation Trend
  const trendData = useMemo(() => {
    const map = {};
    tasks.forEach(t => {
      const date = new Date(t.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
      if (!map[date]) map[date] = { date, created: 0 };
      map[date].created++;
    });
    return Object.values(map).slice(-14);
  }, [tasks]);

  // Chart 4: Priority Breakdown
  const priorityData = useMemo(() => {
    const counts = { low: 0, medium: 0, high: 0, urgent: 0 };
    tasks.forEach(t => {
      const p = t.priority || 'medium';
      if (counts[p] !== undefined) counts[p]++;
    });
    return Object.keys(counts).map(key => ({
      name: key.charAt(0).toUpperCase() + key.slice(1),
      value: counts[key],
      color: PRIORITY_COLORS[key]
    }));
  }, [tasks]);


  if (loadingProject || loadingTasks) {
    return (
      <div className={styles.container}>
        <div className={styles.emptyState}>Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.titleGroup}>
          <h1>Analytics: {project?.name}</h1>
          <p className={styles.subtitle}>Real-time project performance metrics</p>
        </div>
        <div className={styles.controls}>
          <select 
             className={styles.dateSelect}
             value={timeRange}
             onChange={(e) => setTimeRange(e.target.value)}
          >
             <option value="all">All Time</option>
             <option value="30d">Last 30 Days</option>
          </select>
        </div>
      </div>

      {/* Metrics Row (Responsive Class Used Here) */}
      <div className={styles.metricsRow}>
        <MetricCard 
           label="Completion" 
           value={`${stats.progress_percentage || 0}%`} 
           icon={CheckCircle2} 
           theme="green" 
        />
        <MetricCard 
           label="Total Tasks" 
           value={stats.total_tasks} 
           icon={Activity} 
           theme="blue" 
        />
        <MetricCard 
           label="Active Days" 
           value={stats.days_active || 1} 
           icon={Clock} 
           theme="purple" 
        />
        <MetricCard 
           label="Team Size" 
           value={stats.total_members} 
           icon={Users} 
           theme="orange" 
        />
      </div>

      {/* Charts Grid */}
      <div className={styles.grid}>
        
        {/* 1. Status Distribution */}
        <div className={styles.card}>
           <div className={styles.cardHeader}>
             <h3 className={styles.cardTitle}>Task Status</h3>
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
                   <Legend verticalAlign="bottom" height={36} />
                 </PieChart>
               </ResponsiveContainer>
             ) : (
               <div className={styles.emptyState}>No task data available.</div>
             )}
           </div>
        </div>

        {/* 2. Priority Breakdown */}
        <div className={styles.card}>
           <div className={styles.cardHeader}>
             <h3 className={styles.cardTitle}>Task Priorities</h3>
           </div>
           <div className={styles.chartContainer}>
             {priorityData.some(d => d.value > 0) ? (
               <ResponsiveContainer width="100%" height="100%">
                 <BarChart data={priorityData} layout="vertical" margin={{ left: 10 }}>
                   <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                   <XAxis type="number" hide />
                   <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} width={80} tick={{fontSize:12}} />
                   <Tooltip cursor={{fill: 'transparent'}} />
                   <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={24}>
                      {priorityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                   </Bar>
                 </BarChart>
               </ResponsiveContainer>
             ) : (
               <div className={styles.emptyState}>No priority data available.</div>
             )}
           </div>
        </div>

        {/* 3. Member Performance */}
        <div className={styles.card}>
           <div className={styles.cardHeader}>
             <h3 className={styles.cardTitle}>Member Workload</h3>
           </div>
           <div className={styles.chartContainer}>
             {memberData.length > 0 ? (
               <ResponsiveContainer width="100%" height="100%">
                 <BarChart data={memberData}>
                   <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                   <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill:'#94a3b8', fontSize:12}} />
                   <YAxis axisLine={false} tickLine={false} />
                   <Tooltip />
                   <Legend />
                   <Bar dataKey="tasks" name="Total Assigned" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                   <Bar dataKey="completed" name="Completed" fill="#10b981" radius={[4, 4, 0, 0]} />
                 </BarChart>
               </ResponsiveContainer>
             ) : (
               <div className={styles.emptyState}>No member data available.</div>
             )}
           </div>
        </div>

        {/* 4. Task Activity Trend */}
        <div className={styles.card}>
           <div className={styles.cardHeader}>
             <h3 className={styles.cardTitle}>Creation Trend</h3>
           </div>
           <div className={styles.chartContainer}>
             {trendData.length > 0 ? (
               <ResponsiveContainer width="100%" height="100%">
                 <AreaChart data={trendData}>
                   <defs>
                     <linearGradient id="colorCreated" x1="0" y1="0" x2="0" y2="1">
                       <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.1}/>
                       <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                     </linearGradient>
                   </defs>
                   <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                   <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fill:'#94a3b8', fontSize:12}} />
                   <YAxis axisLine={false} tickLine={false} />
                   <Tooltip />
                   <Area type="monotone" dataKey="created" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorCreated)" />
                 </AreaChart>
               </ResponsiveContainer>
             ) : (
               <div className={styles.emptyState}>No recent activity data.</div>
             )}
           </div>
        </div>

      </div>
    </div>
  );
};

// --- Helper Components ---
const MetricCard = ({ label, value, icon: Icon, theme }) => {
  const themeColors = {
    green: { bg: '#ecfdf5', text: '#10b981' },
    blue: { bg: '#eff6ff', text: '#3b82f6' },
    purple: { bg: '#f5f3ff', text: '#8b5cf6' },
    orange: { bg: '#fff7ed', text: '#f97316' }
  };
  const c = themeColors[theme] || themeColors.blue;

  // Uses .metricCard class from module, ensuring it respects the flex-row layout
  return (
    <div className={styles.metricCard}>
      <div style={{ padding: '0.75rem', borderRadius: '12px', background: c.bg, color: c.text }}>
         <Icon size={24} />
      </div>
      <div>
         <div className={styles.metricLabel}>{label}</div>
         <div className={styles.metricValue}>{value}</div>
      </div>
    </div>
  );
};

export default ProjectAnalytics;