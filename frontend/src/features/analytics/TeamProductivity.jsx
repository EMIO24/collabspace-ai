import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Users, TrendingUp } from 'lucide-react';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import styles from './TeamProductivity.module.css';

const TeamProductivity = () => {
  const { currentWorkspace } = useWorkspace();
  const workspaceId = currentWorkspace?.id;

  const { data, isLoading } = useQuery({
    queryKey: ['teamProductivity', workspaceId],
    queryFn: async () => {
      const res = await api.get(`/analytics/workspace/${workspaceId}/team-productivity/`);
      return res.data;
    },
    enabled: !!workspaceId
  });

  if (!workspaceId) return null;
  if (isLoading) return <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading productivity data...</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.iconBox}>
          <Users size={24} />
        </div>
        <div>
          <h2 className={styles.title}>Team Productivity</h2>
          <p className={styles.subtitle}>Task completion and velocity by member</p>
        </div>
      </div>

      <div className={styles.card}>
        <h3 className={styles.cardHeader}>
          <TrendingUp size={16} /> Velocity per Member
        </h3>
        <div className={styles.chartWrapper}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(0,0,0,0.05)" />
              <XAxis type="number" hide />
              <YAxis 
                dataKey="name" 
                type="category" 
                axisLine={false} 
                tickLine={false} 
                width={100}
                tick={{ fill: '#64748b', fontSize: 12 }} 
              />
              <Tooltip 
                cursor={{ fill: 'rgba(0,0,0,0.03)' }}
                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
              />
              <Bar dataKey="tasks_completed" name="Tasks Completed" radius={[0, 4, 4, 0]} barSize={20}>
                {data?.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#6366f1' : '#8b5cf6'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default TeamProductivity;