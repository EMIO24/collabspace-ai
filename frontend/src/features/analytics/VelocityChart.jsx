import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { aiService } from '../../services/aiService';
import styles from './AnalyticsComponents.module.css';

const VelocityChart = ({ projectId }) => {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    
    const fetchData = async () => {
      setIsLoading(true);
      const res = await aiService.getVelocity(projectId);
      
      if (isMounted) {
        // Handle different response structures gracefully
        const chartData = Array.isArray(res) ? res : (res?.velocity_trend || []);
        setData(chartData);
        setIsLoading(false);
      }
    };

    if (projectId) fetchData();

    return () => { isMounted = false; };
  }, [projectId]);

  if (isLoading) {
    return (
      <div className={styles.card}>
        <h3 className={styles.title}>Team Velocity</h3>
        <div className={styles.chartContainer}>
          <div className={styles.loading}>Loading velocity data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>Team Velocity</h3>
      <div className={styles.chartContainer}>
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis 
                dataKey="week" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#94a3b8', fontSize: 12 }} 
                padding={{ left: 10, right: 10 }}
              />
              <YAxis 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#94a3b8', fontSize: 12 }} 
              />
              <Tooltip 
                contentStyle={{ 
                  borderRadius: '12px', 
                  border: '1px solid #e2e8f0', 
                  boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' 
                }} 
              />
              <Line 
                type="monotone" 
                dataKey="completed_tasks" 
                stroke="#6366f1" 
                strokeWidth={3} 
                dot={{ r: 4, fill: '#6366f1', strokeWidth: 2, stroke: '#fff' }}
                activeDot={{ r: 6 }} 
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className={styles.loading}>No velocity data recorded yet.</div>
        )}
      </div>
    </div>
  );
};

export default VelocityChart;