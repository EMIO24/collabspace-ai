import React, { useState } from 'react';
import { Sparkles, MessageSquare, Zap, Code } from 'lucide-react';
import styles from '../features/ai/AIHub.module.css';

// Sub-components
import AIMeetingProcessor from '../features/ai/AIMeetingProcessor';
import AITaskPlayground from '../features/ai/AITaskPlayground';
import AICodeAssistant from '../features/ai/AICodeAssistant';

const TOOLS = [
  { id: 'meetings', title: 'Meetings', desc: 'Summarize & extract actions.', icon: MessageSquare, color: 'green' },
  { id: 'tasks', title: 'Task Ops', desc: 'Breakdown & estimate tasks.', icon: Zap, color: 'orange' },
  { id: 'code', title: 'Code Assistant', desc: 'Review, Refactor & Test.', icon: Code, color: 'blue' },
];

const AIHubPage = () => {
  const [activeTool, setActiveTool] = useState('meetings');

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
        {activeTool === 'meetings' && <AIMeetingProcessor />}
        {activeTool === 'tasks' && <AITaskPlayground />}
        {activeTool === 'code' && <AICodeAssistant />}
      </div>
    </div>
  );
};

export default AIHubPage;