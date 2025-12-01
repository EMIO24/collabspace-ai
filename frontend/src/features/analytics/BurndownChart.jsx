import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { api } from '../../services/api';
import styles from './BurndownChart.module.css';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className={styles.tooltip}>
        <p className={styles.tooltipLabel}>{label}</p>
        {payload.map((entry, index) => (
          <div key={index} className={styles.tooltipItem} style={{ color: entry.color }}>
            <span>●</span>
            {entry.name}: {entry.value} pts
          </div>
        ))}
      </div>
    );
  }
  return null;
};

const BurndownChart = ({ projectId }) => {
  const { data: chartData, isLoading } = useQuery({
    queryKey: ['burndown', projectId],
    queryFn: async () => {
      const res = await api.get(`/analytics/project/${projectId}/burndown/`);
      return res.data; // Expecting [{ date: '...', remaining: 50, ideal: 45 }]
    },
    enabled: !!projectId
  });

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className="flex items-center justify-center h-[400px] text-gray-400">
          Loading Burndown Chart...
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Project Burndown</h3>
        <p className={styles.subtitle}>Remaining effort vs. ideal timeline</p>
      </div>

      <div className={styles.chartArea}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
            <XAxis 
              dataKey="date" 
              stroke="var(--text-muted)" 
              fontSize={12} 
              tickMargin={10} 
            />
            <YAxis 
              stroke="var(--text-muted)" 
              fontSize={12} 
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            
            <Line 
              type="monotone" 
              dataKey="ideal" 
              stroke="#cbd5e1" 
              strokeDasharray="5 5" 
              name="Ideal Burndown" 
              dot={false}
              strokeWidth={2}
            />
            <Line 
              type="monotone" 
              dataKey="remaining" 
              stroke="var(--primary)" 
              activeDot={{ r: 6 }} 
              name="Actual Remaining" 
              strokeWidth={3}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default BurndownChart;