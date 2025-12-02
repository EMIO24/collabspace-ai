import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useWorkspace } from '../../context/WorkspaceContext';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, ComposedChart 
} from 'recharts';
import { Flame, TrendingUp, AlertTriangle, Sparkles } from 'lucide-react';
import { api } from '../../services/api';
import styles from './AIAnalyticsDashboard.module.css';

const AIAnalyticsDashboard = () => {
  const { currentWorkspace } = useWorkspace();
  const workspaceId = currentWorkspace?.id;
  // Assuming a default project ID for the forecast demo, or fetch from context
  const projectId = "active-project-uuid"; 

  // 1. Burnout Data
  const { data: burnoutData, isLoading: burnoutLoading } = useQuery({
    queryKey: ['aiBurnout', workspaceId],
    queryFn: async () => {
      const res = await api.get(`/ai/analytics/burnout-detection/${workspaceId}/`);
      return res.data; // Expected: [{ user: { name, avatar }, risk_score: 85, workload: 'High' }]
    },
    enabled: !!workspaceId
  });

  // 2. Forecast Data
  const { data: forecastData, isLoading: forecastLoading } = useQuery({
    queryKey: ['aiForecast', projectId],
    queryFn: async () => {
      const res = await api.get(`/ai/analytics/project-forecast/${projectId}/`);
      return res.data; 
      // Expected: [{ date: '2023-11-01', actual: 20, projected: 20, lower_bound: 18, upper_bound: 22 }]
    },
    enabled: !!projectId
  });

  const getRiskClass = (score) => {
    if (score > 75) return styles.riskHigh;
    if (score > 40) return styles.riskMedium;
    return styles.riskLow;
  };

  return (
    <div className={styles.grid}>
      
      {/* --- Card 1: Burnout Heatmap --- */}
      <div className={styles.card}>
        <div className={styles.header}>
          <div className={styles.titleGroup}>
            <div className={styles.iconBox} style={{ color: '#ef4444' }}>
              <Flame size={24} />
            </div>
            <div>
              <h3 className={styles.title}>Team Burnout Detection</h3>
              <p className={styles.desc}>AI analysis of workload, hours, and activity patterns.</p>
            </div>
          </div>
          <Sparkles size={20} className="text-purple-500 animate-pulse" />
        </div>

        {burnoutLoading ? (
          <div>Analyzing team patterns...</div>
        ) : (
          <div className={styles.heatmap}>
            {burnoutData?.map((item, idx) => (
              <div key={idx} className={`${styles.heatItem} ${getRiskClass(item.risk_score)}`}>
                <img 
                  src={item.user.avatar || `https://ui-avatars.com/api/?name=${item.user.name}`} 
                  alt={item.user.name} 
                  className={styles.heatAvatar} 
                />
                <span className={styles.heatName}>{item.user.name}</span>
                <span className={styles.heatScore}>{item.risk_score}% Risk</span>
              </div>
            ))}
            {!burnoutData?.length && <div className="text-gray-400">No data available</div>}
          </div>
        )}
      </div>

      {/* --- Card 2: AI Project Forecast --- */}
      <div className={styles.card}>
        <div className={styles.header}>
          <div className={styles.titleGroup}>
            <div className={styles.iconBox} style={{ color: '#3b82f6' }}>
              <TrendingUp size={24} />
            </div>
            <div>
              <h3 className={styles.title}>Completion Forecast</h3>
              <p className={styles.desc}>Predictive modeling based on current velocity.</p>
            </div>
          </div>
          <div className="flex items-center gap-1 text-xs text-orange-600 bg-orange-50 px-2 py-1 rounded">
            <AlertTriangle size={12} />
            <span>AI Confidence: 85%</span>
          </div>
        </div>

        <div className={styles.chartContainer}>
          {forecastLoading ? (
            <div>Generating forecast...</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={forecastData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
                <XAxis dataKey="date" fontSize={12} tickMargin={10} stroke="#94a3b8" />
                <YAxis fontSize={12} stroke="#94a3b8" />
                <Tooltip 
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                />
                <Legend />
                {/* Confidence Interval (Area) */}
                <Area 
                  type="monotone" 
                  dataKey="range" 
                  fill="#e0e7ff" 
                  stroke="none" 
                  name="Confidence Range" 
                />
                <Line 
                  type="monotone" 
                  dataKey="actual" 
                  stroke="#3b82f6" 
                  strokeWidth={3} 
                  name="Actual Progress" 
                />
                <Line 
                  type="monotone" 
                  dataKey="projected" 
                  stroke="#8b5cf6" 
                  strokeDasharray="5 5" 
                  strokeWidth={2} 
                  name="AI Projection" 
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

    </div>
  );
};

export default AIAnalyticsDashboard;