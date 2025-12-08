import React, { useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { 
  Sparkles, AlertTriangle, TrendingUp, Users, 
  Zap, AlertCircle, RefreshCw
} from 'lucide-react';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import Button from '../../components/ui/Button/Button';
import styles from './AIAnalyticsDashboard.module.css';
import { toast } from 'react-hot-toast';

const AIAnalyticsDashboard = () => {
  const { currentWorkspace } = useWorkspace();
  const workspaceId = currentWorkspace?.id;
  const projectId = "9639d0c5-a58e-4f3b-8d47-27d2b209790e"; 

  // --- DATA FETCHING ---

  // 1. Forecast
  const { data: forecast, isLoading: loadingForecast, refetch: refetchForecast } = useQuery({
    queryKey: ['aiForecast', projectId],
    queryFn: async () => {
        try { return (await api.get(`/ai/analytics/project-forecast/${projectId}/`)).data; }
        catch { return null; }
    },
    enabled: !!projectId
  });

  // 2. Burnout
  const { data: burnout, isLoading: loadingBurnout, refetch: refetchBurnout } = useQuery({
    queryKey: ['aiBurnout', workspaceId],
    queryFn: async () => {
        try { return (await api.get(`/ai/analytics/burnout-detection/${workspaceId}/`)).data; }
        catch { return null; }
    },
    enabled: !!workspaceId
  });

  // 3. Velocity
  const { data: velocity, isLoading: loadingVelocity, refetch: refetchVelocity } = useQuery({
    queryKey: ['aiVelocity', projectId],
    queryFn: async () => {
        try { return (await api.get(`/ai/analytics/velocity/${projectId}/`)).data; }
        catch { return null; }
    },
    enabled: !!projectId
  });

  // 4. Bottlenecks
  const { data: bottlenecks, isLoading: loadingBottlenecks, refetch: refetchBottlenecks } = useQuery({
    queryKey: ['aiBottlenecks', projectId],
    queryFn: async () => {
        try { return (await api.get(`/ai/analytics/bottlenecks/${projectId}/`)).data; }
        catch { return null; }
    },
    enabled: !!projectId
  });

  const handleRefresh = () => {
    refetchForecast();
    refetchBurnout();
    refetchVelocity();
    refetchBottlenecks();
    toast.success('Refreshing insights...');
  };

  // Helper to render Markdown-like text safely
  const renderAnalysis = (text) => {
    if (!text) return <div className={styles.emptyState}>No analysis available.</div>;
    return text.split('\n').map((line, i) => {
        if (line.startsWith('**') || line.startsWith('###')) {
            return <div key={i} className={styles.analysisHeader}>{line.replace(/\*|#/g, '')}</div>;
        }
        if (line.trim().startsWith('*')) {
            return <div key={i} className={styles.analysisList}>• {line.replace('*', '')}</div>;
        }
        if (line.trim() === '') return <br key={i}/>;
        return <div key={i} className={styles.analysisText}>{line}</div>;
    });
  };

  if (!workspaceId) return <div className={styles.loadingState}>Please select a workspace.</div>;

  return (
    <div className={styles.container}>
      
      {/* --- Header --- */}
      <div className={styles.header}>
        <div className={styles.titleGroup}>
          <h1>
            <Sparkles className={styles.iconPurple} /> 
            AI Insights
          </h1>
          <p className={styles.subtitle}>Real-time predictive analysis & risk detection</p>
        </div>
        <div className={styles.controls}>
          <Button onClick={handleRefresh} variant="outline">
            <RefreshCw size={16} className="mr-2" /> Refresh Analysis
          </Button>
        </div>
      </div>

      <div className={styles.grid}>
        
        {/* 1. Project Forecast */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
             <h3 className={styles.title}><TrendingUp size={20} className={styles.iconBlue} /> Project Forecast</h3>
          </div>
          <div className={styles.analysisContainer}>
             {loadingForecast ? <div className={styles.skeletonText} /> : renderAnalysis(forecast?.forecast)}
          </div>
        </div>

        {/* 2. Burnout Detection */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
             <h3 className={styles.title}><Zap size={20} className={styles.iconOrange} /> Burnout Detection</h3>
          </div>
          <div className={styles.analysisContainer}>
             {loadingBurnout ? <div className={styles.skeletonText} /> : renderAnalysis(burnout?.burnout_analysis)}
          </div>
        </div>

        {/* 3. Bottleneck Identification */}
        <div className={styles.card}>
           <div className={styles.cardHeader}>
             <h3 className={styles.title}><AlertCircle size={20} className={styles.iconRed} /> Bottleneck Analysis</h3>
           </div>
           <div className={styles.analysisContainer}>
             {loadingBottlenecks ? <div className={styles.skeletonText} /> : renderAnalysis(bottlenecks?.bottlenecks)}
           </div>
        </div>

        {/* 4. Velocity Analysis */}
        <div className={styles.card}>
           <div className={styles.cardHeader}>
             <h3 className={styles.title}><Users size={20} className={styles.iconGreen} /> Team Velocity</h3>
           </div>
           <div className={styles.analysisContainer}>
             {loadingVelocity ? <div className={styles.skeletonText} /> : renderAnalysis(velocity?.velocity_analysis)}
           </div>
        </div>

      </div>
    </div>
  );
};

export default AIAnalyticsDashboard;