import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Sparkles, ListTodo, BarChart2, Calendar, Clock, 
  User, CheckSquare, Upload, Play, Share2, Bold, Italic, Link as LinkIcon
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Avatar from '../../components/ui/Avatar/Avatar';
import Button from '../../components/ui/Button/Button';
import styles from './MeetingDetail.module.css';

const MeetingDetail = () => {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [noteContent, setNoteContent] = useState('');
  
  // 1. Fetch Meeting Details
  const { data: meeting, isLoading } = useQuery({
    queryKey: ['meeting', id],
    queryFn: async () => (await api.get(`/ai/meetings/${id}/`)).data,
    enabled: !!id
  });

  // Auto-fill editor
  useEffect(() => {
    if (meeting?.transcript) {
        // If transcript is array, join it, else use as string
        const text = Array.isArray(meeting.transcript) 
            ? meeting.transcript.map(t => `${t.speaker}: ${t.text}`).join('\n\n')
            : meeting.transcript;
        setNoteContent(text || '');
    }
  }, [meeting]);

  // --- AI Mutations ---
  const summarizeMutation = useMutation({
    mutationFn: () => api.post('/ai/meetings/summarize/', { transcript: noteContent }),
    onSuccess: (res) => {
        // Optimistically update the cache with new summary
        queryClient.setQueryData(['meeting', id], old => ({ ...old, summary: res.data.summary }));
        toast.success('Summary generated');
    }
  });

  const extractActionItemsMutation = useMutation({
    mutationFn: () => api.post('/ai/meetings/action-items/', { transcript: noteContent }),
    onSuccess: (res) => {
        queryClient.setQueryData(['meeting', id], old => ({ ...old, action_items: res.data.action_items }));
        toast.success('Action items extracted');
    }
  });

  const analyzeSentimentMutation = useMutation({
    mutationFn: () => api.post('/ai/meetings/sentiment/', { transcript: noteContent }),
    onSuccess: (res) => {
        queryClient.setQueryData(['meeting', id], old => ({ ...old, sentiment_analysis: res.data }));
        toast.success('Sentiment analyzed');
    }
  });

  const createTaskMutation = useMutation({
    mutationFn: (taskItem) => api.post('/tasks/tasks/', {
        title: taskItem,
        status: 'todo',
        priority: 'medium',
        project: meeting?.project_id // if available
    }),
    onSuccess: () => toast.success('Task created from action item')
  });

  // Auto-Save Simulation
  useEffect(() => {
    const timer = setTimeout(() => {
        // In real app: api.put(`/meetings/${id}/notes`, { content: noteContent })
        console.log('Auto-saving notes...');
    }, 30000);
    return () => clearTimeout(timer);
  }, [noteContent]);

  if (isLoading) return <div className="p-10 text-center text-gray-500">Loading meeting...</div>;
  if (!meeting) return <div className="p-10 text-center text-gray-500">Meeting not found</div>;

  return (
    <div className={styles.container}>
      
      {/* LEFT: EDITOR */}
      <div className={styles.editorPanel}>
        <div className={styles.editorHeader}>
           <input className={styles.meetingTitle} defaultValue={meeting.title} />
           <div className={styles.metaRow}>
              <span className={styles.metaItem}><Calendar size={14}/> {new Date(meeting.date).toLocaleDateString()}</span>
              <span className={styles.metaItem}><Clock size={14}/> {meeting.duration} min</span>
              <button className="text-blue-600 font-semibold hover:underline">Share</button>
           </div>
        </div>

        <div className={styles.participants}>
           {/* Mock Participants if not in API */}
           {(meeting.participants || ['Alice', 'Bob', 'Charlie']).map((p, i) => (
             <div key={i} className="flex items-center gap-2 bg-gray-100 px-3 py-1 rounded-full">
                <Avatar size="xs" fallback={p[0]} />
                <span className="text-xs font-medium text-gray-700">{p}</span>
             </div>
           ))}
           <button className="w-8 h-8 rounded-full border border-dashed border-gray-300 flex items-center justify-center text-gray-400 hover:border-blue-500 hover:text-blue-500">
             <User size={14} />
           </button>
        </div>

        <div className={styles.toolbar}>
           <button className={styles.toolBtn}><Bold size={16} /></button>
           <button className={styles.toolBtn}><Italic size={16} /></button>
           <button className={styles.toolBtn}><LinkIcon size={16} /></button>
           <div className="w-px h-4 bg-gray-300 mx-2" />
           <button className={styles.toolBtn}><Upload size={16} /> Recording</button>
        </div>

        <textarea 
          className={styles.editorArea} 
          value={noteContent}
          onChange={(e) => setNoteContent(e.target.value)}
          placeholder="Start typing or upload a recording to transcribe..."
        />

        <div className={styles.agendaSection}>
           <h4 className={styles.sectionTitle}>Agenda</h4>
           <div className={styles.agendaItem}>
              <input type="checkbox" defaultChecked className="accent-blue-600" />
              <span className="text-sm text-gray-600 line-through">Project Kickoff</span>
           </div>
           <div className={styles.agendaItem}>
              <input type="checkbox" className="accent-blue-600" />
              <span className="text-sm text-gray-800">Review Q3 Goals</span>
           </div>
        </div>
      </div>

      {/* RIGHT: AI INSIGHTS */}
      <div className={styles.insightsPanel}>
        <div className={styles.aiHeader}>
           <button 
             className={`${styles.aiBtn} ${styles.btnPurple}`}
             onClick={() => summarizeMutation.mutate()}
             disabled={summarizeMutation.isPending}
           >
              <Sparkles size={16} /> {summarizeMutation.isPending ? 'Summarizing...' : 'Summarize'}
           </button>
           <button 
             className={`${styles.aiBtn} ${styles.btnBlue}`}
             onClick={() => extractActionItemsMutation.mutate()}
             disabled={extractActionItemsMutation.isPending}
           >
              <ListTodo size={16} /> Action Items
           </button>
           <button 
             className={`${styles.aiBtn} ${styles.btnBlue}`}
             onClick={() => analyzeSentimentMutation.mutate()}
             disabled={analyzeSentimentMutation.isPending}
           >
              <BarChart2 size={16} /> Sentiment
           </button>
        </div>

        {/* 1. Summary Card */}
        {meeting.summary && (
          <div className={styles.insightCard}>
             <div className={styles.insightHeader}>
                <Sparkles size={18} className="text-purple-600" /> Executive Summary
             </div>
             <div className={styles.summaryText}>
                {/* Check if summary is array or string */}
                {Array.isArray(meeting.summary) ? (
                   <ul>{meeting.summary.map((s, i) => <li key={i}>{s}</li>)}</ul>
                ) : (
                   <p className="text-sm text-gray-600 leading-relaxed">{meeting.summary}</p>
                )}
             </div>
          </div>
        )}

        {/* 2. Action Items Card */}
        {meeting.action_items && (
          <div className={styles.insightCard}>
             <div className={styles.insightHeader}>
                <CheckSquare size={18} className="text-blue-600" /> Action Items
             </div>
             <div>
                {meeting.action_items.map((item, i) => (
                   <div key={i} className={styles.actionItem}>
                      <input type="checkbox" />
                      <div className={styles.actionContent}>
                         <div className={styles.actionText}>{item}</div>
                         <div className={styles.actionMeta}>
                            <span>Assignee: AI Suggestion</span>
                            <button className={styles.convertBtn} onClick={() => createTaskMutation.mutate(item)}>
                               + Convert to Task
                            </button>
                         </div>
                      </div>
                   </div>
                ))}
             </div>
          </div>
        )}

        {/* 3. Sentiment & Engagement */}
        <div className={styles.insightCard}>
           <div className={styles.insightHeader}>
              <BarChart2 size={18} className="text-orange-500" /> Engagement & Sentiment
           </div>
           
           <div className="mb-6">
              <div className="text-xs font-bold text-gray-400 uppercase mb-2">Overall Sentiment</div>
              <div className={styles.sentimentGauge}>
                 <div className={styles.gaugePos} style={{ width: '60%' }} />
                 <div className={styles.gaugeNeu} style={{ width: '30%' }} />
                 <div className={styles.gaugeNeg} style={{ width: '10%' }} />
              </div>
              <div className={styles.sentimentLabel}>
                 <span>Positive (60%)</span>
                 <span>Negative (10%)</span>
              </div>
           </div>

           <div>
              <div className="text-xs font-bold text-gray-400 uppercase mb-2">Speaking Time</div>
              {['Alice', 'Bob', 'Charlie'].map((p, i) => (
                 <div key={i} className={styles.engagementRow}>
                    <span className="text-xs w-16 font-medium text-gray-600">{p}</span>
                    <div className={styles.engageBar}>
                       <div 
                         className={styles.engageFill} 
                         style={{ width: `${[45, 30, 25][i]}%`, opacity: 1 - (i * 0.2) }} 
                       />
                    </div>
                    <span className="text-xs text-gray-400">{[45, 30, 25][i]}%</span>
                 </div>
              ))}
           </div>
        </div>

      </div>
    </div>
  );
};

export default MeetingDetail;