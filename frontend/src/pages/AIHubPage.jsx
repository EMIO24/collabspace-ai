import React, { useState } from 'react';
import { Sparkles, BarChart2, MessageSquare, Zap } from 'lucide-react';
import styles from '../features/ai/AIHub.module.css';

// Sub-components
import AIAnalyticsDashboard from '../features/ai/AIAnalyticsDashboard';
import AIMeetingProcessor from '../features/ai/AIMeetingProcessor';
import AITaskPlayground from '../features/ai/AITaskPlayground';

const TOOLS = [
  { id: 'analytics', title: 'Analytics', desc: 'Forecasts & Burnout detection.', icon: BarChart2, color: 'purple' },
  { id: 'meetings', title: 'Meetings', desc: 'Summarize & extract actions.', icon: MessageSquare, color: 'green' },
  { id: 'tasks', title: 'Task Ops', desc: 'Breakdown & estimate tasks.', icon: Zap, color: 'orange' },
];

const AIHubPage = () => {
  const [activeTool, setActiveTool] = useState('analytics');

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          <Sparkles className="text-yellow-500 fill-yellow-500" /> AI Hub
        </h1>
        <p className={styles.subtitle}>Central command for all AI-powered capabilities.</p>
      </div>

      <div className={styles.navGrid}>
        {TOOLS.map((tool) => (
          <div 
            key={tool.id}
            className={`${styles.navCard} ${activeTool === tool.id ? styles.activeCard : ''}`}
            onClick={() => setActiveTool(tool.id)}
          >
            <div className={`${styles.iconBox} ${styles[tool.color]}`}>
              <tool.icon size={24} />
            </div>
            <div>
              <h3 className={styles.navTitle}>{tool.title}</h3>
              <p className={styles.navDesc}>{tool.desc}</p>
            </div>
          </div>
        ))}
      </div>

      <div className={styles.content}>
        {activeTool === 'analytics' && <AIAnalyticsDashboard />}
        {activeTool === 'meetings' && <AIMeetingProcessor />}
        {activeTool === 'tasks' && <AITaskPlayground />}
      </div>
    </div>
  );
};

export default AIHubPage;