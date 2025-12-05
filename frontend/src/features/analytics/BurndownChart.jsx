import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { api } from '../../services/api';
import styles from './BurndownChart.module.css';

const BurndownChart = ({ projectId, startDate, endDate }) => {
  const defaultStart = new Date();
  defaultStart.setDate(defaultStart.getDate() - 14);
  const defaultEnd = new Date();

  const startStr = startDate ? new Date(startDate).toISOString().split('T')[0] : defaultStart.toISOString().split('T')[0];
  const endStr = endDate ? new Date(endDate).toISOString().split('T')[0] : defaultEnd.toISOString().split('T')[0];

  const { data: chartData, isLoading } = useQuery({
    queryKey: ['burndown', projectId, startStr, endStr],
    queryFn: async () => {
      try {
        const params = new URLSearchParams({
          sprint_start: startStr,
          sprint_end: endStr
        });
        const res = await api.get(`/analytics/project/${projectId}/burndown/?${params.toString()}`);
        return res.data;
      } catch (e) {
        return null; 
      }
    },
    enabled: !!projectId,
    retry: 0
  });

  const mockData = [
    { date: 'Day 1', ideal: 100, remaining: 100 },
    { date: 'Day 5', ideal: 80, remaining: 85 },
    { date: 'Day 10', ideal: 40, remaining: 50 },
    { date: 'Day 14', ideal: 0, remaining: 20 },
  ];

  const displayData = (chartData && chartData.length > 0) ? chartData : mockData;
  const isMock = !chartData || chartData.length === 0;

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingState}>
          Loading Chart...
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Project Burndown</h3>
        <p className={styles.subtitle}>
           {isMock ? "Sample projection (Data unavailable)" : `Progress: ${startStr} to ${endStr}`}
        </p>
      </div>

      <div className={styles.chartArea}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={displayData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
            <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} />
            <YAxis stroke="#94a3b8" fontSize={12} />
            <Tooltip 
              contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 20px rgba(0,0,0,0.1)' }}
            />
            <Legend />
            
            <Line 
              type="monotone" 
              dataKey="ideal" 
              stroke="#cbd5e1" 
              strokeDasharray="5 5" 
              name="Ideal" 
              dot={false}
            />
            <Line 
              type="monotone" 
              dataKey="remaining" 
              stroke="#6366f1" 
              activeDot={{ r: 6 }} 
              name="Remaining" 
              strokeWidth={3}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default BurndownChart;