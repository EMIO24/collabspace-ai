import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Bot, FileText, Sparkles, CheckSquare, Calendar, Clock, Mic } from 'lucide-react';
import { api } from '../../services/api';
import styles from './MeetingIntelligence.module.css';

const MeetingIntelligence = () => {
  const [selectedId, setSelectedId] = useState(null);

  // 1. Fetch List
  const { data: meetings, isLoading: listLoading } = useQuery({
    queryKey: ['meetings'],
    queryFn: async () => (await api.get('/ai/meetings/')).data
  });

  // 2. Fetch Details (Dependent on selection)
  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ['meeting', selectedId],
    queryFn: async () => (await api.get(`/ai/meetings/${selectedId}/`)).data,
    enabled: !!selectedId
  });

  const getSentimentClass = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return styles.positive;
      case 'negative': return styles.negative;
      default: return styles.neutral;
    }
  };

  return (
    <div className={styles.container}>
      {/* Sidebar List */}
      <div className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <h2 className={styles.title}>
            <Bot size={24} className="text-purple-600" /> 
            Meeting Intelligence
          </h2>
        </div>
        <div className={styles.list}>
          {listLoading ? (
            <div className="p-4 text-center text-gray-400">Loading...</div>
          ) : meetings?.map((meeting) => (
            <div 
              key={meeting.id}
              className={`${styles.card} ${selectedId === meeting.id ? styles.cardActive : ''}`}
              onClick={() => setSelectedId(meeting.id)}
            >
              <h3 className={styles.cardTitle}>{meeting.title}</h3>
              <div className={styles.cardMeta}>
                <span>{new Date(meeting.date).toLocaleDateString()}</span>
                <span className={`${styles.sentiment} ${getSentimentClass(meeting.sentiment)}`}>
                  {meeting.sentiment || 'Neutral'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detail View */}
      <div className={styles.detail}>
        {!selectedId ? (
          <div className={styles.emptyState}>
            <Bot size={64} className="mb-4 text-purple-200" />
            <p>Select a meeting to view AI insights</p>
          </div>
        ) : detailLoading ? (
          <div className={styles.emptyState}>Analyzing transcript...</div>
        ) : detail ? (
          <>
            <div className={styles.detailHeader}>
              <h1 className={styles.detailTitle}>{detail.title}</h1>
              <div className={styles.detailMeta}>
                <span className="flex items-center gap-1"><Calendar size={14}/> {new Date(detail.date).toLocaleDateString()}</span>
                <span className="flex items-center gap-1"><Clock size={14}/> {detail.duration} min</span>
              </div>
            </div>

            <div className={styles.contentGrid}>
              {/* Left: Transcript */}
              <div className={`${styles.column} ${styles.columnLeft}`}>
                <h3 className={styles.columnHeader}>
                  <Mic size={18} className="text-gray-400" /> Full Transcript
                </h3>
                <div className={styles.transcriptText}>
                  {/* Mocking transcript format if string or array */}
                  {Array.isArray(detail.transcript) 
                    ? detail.transcript.map((line, i) => (
                        <p key={i} className="mb-2">
                          <span className={styles.speaker}>{line.speaker}:</span>
                          {line.text}
                        </p>
                      ))
                    : detail.transcript
                  }
                </div>
              </div>

              {/* Right: AI Insights */}
              <div className={styles.column}>
                <div className={styles.aiSection}>
                  <h3 className={styles.columnHeader} style={{ color: '#7c3aed' }}>
                    <Sparkles size={18} /> AI Summary
                  </h3>
                  <ul className={styles.summaryList}>
                    {detail.summary?.map((point, i) => (
                      <li key={i}>{point}</li>
                    ))}
                  </ul>
                </div>

                <div className={styles.aiSection} style={{ background: 'rgba(255,255,255,0.6)', borderColor: 'var(--glass-border)' }}>
                  <h3 className={styles.columnHeader}>
                    <CheckSquare size={18} className="text-blue-500" /> Action Items
                  </h3>
                  {detail.action_items?.map((item, i) => (
                    <div key={i} className={styles.actionItem}>
                      <input type="checkbox" className="mt-1" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
};

export default MeetingIntelligence;