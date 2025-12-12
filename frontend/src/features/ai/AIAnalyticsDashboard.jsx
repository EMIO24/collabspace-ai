import React, { useState, useMemo, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, ComposedChart 
} from 'recharts';
import { 
  Sparkles, TrendingUp, Zap, AlertCircle, RefreshCw, 
  Check, Calendar, ArrowRight, Activity, Users // Added Users here
} from 'lucide-react';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import Avatar from '../../components/ui/Avatar/Avatar';
import Button from '../../components/ui/Button/Button';
import styles from './AIAnalyticsDashboard.module.css';
import { toast } from 'react-hot-toast';

const AIAnalyticsDashboard = () => {
  const { currentWorkspace } = useWorkspace();
  const workspaceId = currentWorkspace?.id;
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [dateRange, setDateRange] = useState('30d');
  
  // Optimization Result State (Since it's a mutation response)
  const [optimizationResult, setOptimizationResult] = useState(null);

  // --- DATA FETCHING ---

  // 0. Fetch Projects
  const { data: projects } = useQuery({
    queryKey: ['workspaceProjects', workspaceId],
    queryFn: async () => {
        if (!workspaceId) return [];
        const res = await api.get(`/projects/?workspace=${workspaceId}`);
        return Array.isArray(res.data) ? res.data : (res.data.results || []);
    },
    enabled: !!workspaceId
  });

  // Auto-select project
  useEffect(() => {
    if (projects && projects.length > 0 && !selectedProjectId) {
        setSelectedProjectId(projects[0].id);
    }
  }, [projects, selectedProjectId]);

  // 1. Forecast
  const { data: rawForecast, isLoading: loadingForecast, refetch: refetchForecast } = useQuery({
    queryKey: ['aiForecast', selectedProjectId],
    queryFn: async () => {
        try { return (await api.get(`/ai/analytics/project-forecast/${selectedProjectId}/`)).data; }
        catch { return null; }
    },
    enabled: !!selectedProjectId
  });

  // 2. Burnout
  const { data: rawBurnout, isLoading: loadingBurnout, refetch: refetchBurnout } = useQuery({
    queryKey: ['aiBurnout', workspaceId],
    queryFn: async () => {
        try { return (await api.get(`/ai/analytics/burnout-detection/${workspaceId}/`)).data; }
        catch { return []; }
    },
    enabled: !!workspaceId
  });

  // 3. Velocity
  const { data: rawVelocity, isLoading: loadingVelocity, refetch: refetchVelocity } = useQuery({
    queryKey: ['aiVelocity', selectedProjectId],
    queryFn: async () => {
        try { return (await api.get(`/ai/analytics/velocity/${selectedProjectId}/`)).data; }
        catch { return []; }
    },
    enabled: !!selectedProjectId
  });

  // 4. Bottlenecks
  const { data: bottlenecks, isLoading: loadingBottlenecks, refetch: refetchBottlenecks } = useQuery({
    queryKey: ['aiBottlenecks', selectedProjectId],
    queryFn: async () => {
        try { return (await api.get(`/ai/analytics/bottlenecks/${selectedProjectId}/`)).data; }
        catch { return null; }
    },
    enabled: !!selectedProjectId
  });

  // --- DATA NORMALIZATION ---
  const forecast = useMemo(() => {
    if (!rawForecast) return null;
    return rawForecast.forecast || rawForecast; 
  }, [rawForecast]);

  const burnout = useMemo(() => {
    if (!rawBurnout) return [];
    if (Array.isArray(rawBurnout)) return rawBurnout;
    // Handle array in key if present, otherwise assume text analysis
    if (rawBurnout.burnout_risks) return rawBurnout.burnout_risks;
    return rawBurnout; // Might be object with 'burnout_analysis' text
  }, [rawBurnout]);

  const velocity = useMemo(() => {
    if (!rawVelocity) return [];
    if (Array.isArray(rawVelocity)) return rawVelocity;
    return rawVelocity; // Might be object with 'velocity_analysis' text
  }, [rawVelocity]);

  // Optimization Mutation
  const optimizeMutation = useMutation({
    mutationFn: () => api.post('/ai/analytics/resource-optimizer/', { project_id: selectedProjectId }),
    onSuccess: (res) => {
        setOptimizationResult(res.data.resource_allocation || "Optimization complete.");
        toast.success('Analysis complete');
    },
    onError: () => toast.error('Optimization failed')
  });

  const stages = ['Design', 'Dev', 'Review', 'QA', 'Deploy'];
  
  const handleRefresh = () => {
    refetchForecast();
    refetchBurnout();
    refetchVelocity();
    refetchBottlenecks();
    toast.success('Refreshing insights...');
  };

  // --- SMART TEXT RENDERER ---
  const renderTextAnalysis = (input) => {
    if (!input) return <div className="text-gray-400 italic p-4 text-center">No analysis available.</div>;
    
    // Convert objects to string if needed
    let text = input;
    if (typeof input !== 'string') {
        if (typeof input === 'object' && input.burnout_analysis) text = input.burnout_analysis;
        else if (typeof input === 'object' && input.velocity_analysis) text = input.velocity_analysis;
        else if (typeof input === 'object') text = JSON.stringify(input, null, 2);
        else text = String(input);
    }
    
    const cleanText = text.replace(/\\n/g, '\n').replace(/\*\*/g, '');

    return cleanText.split('\n').map((line, i) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={i} style={{height:'8px'}} />;

        // Key-Value pairs
        if (trimmed.includes(':') && trimmed.length < 60 && !trimmed.startsWith('-') && !trimmed.startsWith('•')) {
            const [key, val] = trimmed.split(':');
            let badgeClass = styles.badgeLow;
            if (key.includes('Score') || key.includes('Risk')) {
                if (val.toLowerCase().includes('high') || val.includes('4/') || val.includes('5/')) badgeClass = styles.badgeHigh;
                else if (val.toLowerCase().includes('medium')) badgeClass = styles.badgeMed;

                return (
                    <div key={i} className={styles.keyMetric}>
                        <span className={styles.keyLabel}>{key}</span>
                        <div className="flex items-center gap-2">
                           <span className={`${styles.badge} ${badgeClass}`}>{val.trim()}</span>
                        </div>
                    </div>
                );
            }
            return (
                <div key={i} className={styles.keyMetric}>
                    <span className={styles.keyLabel}>{key}</span>
                    <span className={styles.keyValue}>{val}</span>
                </div>
            );
        }

        // Headers
        if (trimmed.startsWith('#') || (trimmed.match(/^\d\./) && trimmed.length < 50)) {
            return <h4 key={i} className={styles.sectionHeader}>{trimmed.replace(/#/g, '')}</h4>;
        }

        // Lists
        if (trimmed.startsWith('-') || trimmed.startsWith('•') || trimmed.startsWith('*')) {
            return <div key={i} className={styles.bulletPoint}>{trimmed.replace(/^[-•*]\s*/, '')}</div>;
        }

        // Paragraph
        return <p key={i} style={{marginBottom:'0.5rem'}}>{trimmed}</p>;
    });
  };

  if (!workspaceId) return <div className="p-10 text-center text-gray-500">Please select a workspace.</div>;

  return (
    <div className={styles.container}>
      
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.titleGroup}>
          <h1>
            <Sparkles className={styles.iconPurple} /> 
            AI Insights
          </h1>
          <p className={styles.subtitle}>Predictive analytics & resource optimization</p>
        </div>
        <div className={styles.controls}>
          <select 
             className={styles.select} 
             value={selectedProjectId} 
             onChange={(e) => setSelectedProjectId(e.target.value)}
          >
             {projects?.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <select className={styles.select} value={dateRange} onChange={e => setDateRange(e.target.value)}>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
          <Button onClick={handleRefresh} variant="outline">
            <RefreshCw size={16} className="mr-2" /> Refresh
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
             {loadingForecast ? <div className={styles.skeletonText} /> : renderTextAnalysis(forecast)}
          </div>
        </div>

        {/* 2. Burnout Detection */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
             <h3 className={styles.title}><Zap size={20} className={styles.iconOrange} /> Burnout Detection</h3>
          </div>
          
          {/* Check if array (render grid) or object/text (render analysis) */}
          {Array.isArray(burnout) && burnout.length > 0 ? (
             <div className={styles.memberGrid}>
                 {burnout.map((member, i) => (
                    <div key={i} className={styles.memberItem}>
                       <Avatar src={member.avatar} fallback={member.name?.[0]} />
                       <div className={styles.memberName}>{member.name}</div>
                       <div className={styles.memberStat}>{member.hours}h / week</div>
                       <div className={styles.workloadBar}>
                          <div 
                            className={styles.workloadFill} 
                            style={{ 
                                width: `${Math.min((member.hours / 40) * 100, 100)}%`,
                                background: member.hours > 40 ? '#ef4444' : '#3b82f6'
                            }} 
                          />
                       </div>
                    </div>
                 ))}
             </div>
          ) : (
             <div className={styles.analysisContainer}>
                 {loadingBurnout ? <div className={styles.skeletonText} /> : renderTextAnalysis(burnout)}
             </div>
          )}
        </div>

        {/* 3. Bottleneck Analysis */}
        <div className={`${styles.card} ${styles.fullWidth}`}>
           <div className={styles.cardHeader}>
             <h3 className={styles.title}><AlertCircle size={20} className={styles.iconRed} /> Bottleneck Analysis</h3>
           </div>
           
           {/* If text analysis */}
           {bottlenecks?.bottlenecks ? (
                <div className={styles.analysisContainer}>
                    {renderTextAnalysis(bottlenecks.bottlenecks)}
                </div>
           ) : (
               <div className={styles.processFlow}>
                  {stages.map((stage) => (
                     <div key={stage} className={styles.flowNode}>{stage}</div>
                  ))}
                  <div className="text-center w-full mt-4 text-gray-400 italic">
                      {loadingBottlenecks ? "Analyzing workflow..." : "No bottleneck analysis available."}
                  </div>
               </div>
           )}
        </div>

        {/* 4. Velocity Analysis */}
        <div className={styles.card}>
           <div className={styles.cardHeader}>
             <h3 className={styles.title}><Activity size={20} className={styles.iconGreen} /> Team Velocity</h3>
           </div>
           
           {/* Handle text analysis vs structured data if API provides it later */}
           <div className={styles.analysisContainer}>
               {loadingVelocity ? <div className={styles.skeletonText} /> : renderTextAnalysis(velocity)}
           </div>
        </div>

        {/* 5. Resource Optimizer */}
        <div className={`${styles.card} ${styles.fullWidth}`}>
           <div className={styles.cardHeader}>
             <h3 className={styles.title}><Users size={20} className={styles.iconIndigo} /> Resource Optimizer</h3>
             <Button 
                onClick={() => optimizeMutation.mutate()} 
                isLoading={optimizeMutation.isPending}
                disabled={!selectedProjectId}
             >
                <Sparkles size={16} className="mr-2" /> Run AI Optimization
             </Button>
           </div>

           <div className={styles.analysisContainer}>
               {optimizationResult ? renderTextAnalysis(optimizationResult) : (
                   <div className="text-center text-gray-400 py-8 italic">
                       Click "Run AI Optimization" to analyze workload balance and get reassignment suggestions.
                   </div>
               )}
           </div>
        </div>

      </div>
    </div>
  );
};

export default AIAnalyticsDashboard;