import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { FileText, List, BarChart, Copy, CheckCircle, Mail, User, Calendar } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Button from '../../components/ui/Button/Button';
import styles from './AIMeetingProcessor.module.css';

const AIMeetingProcessor = () => {
  const [notes, setNotes] = useState('');
  const [result, setResult] = useState(null);
  
  const handleSuccess = (type, data) => setResult({ type, content: data });

  // API Mutations
  const summaryMutation = useMutation({
    mutationFn: (text) => api.post('/ai/meetings/summarize/', { transcript: text, participants: ["User"] }),
    onSuccess: (res) => handleSuccess('Summary', res.data)
  });

  const actionItemsMutation = useMutation({
    mutationFn: (text) => api.post('/ai/meetings/action-items/', { transcript: text }),
    onSuccess: (res) => handleSuccess('Action Items', res.data)
  });

  const sentimentMutation = useMutation({
    mutationFn: (text) => api.post('/ai/meetings/sentiment/', { transcript: text }),
    onSuccess: (res) => handleSuccess('Sentiment', res.data)
  });

  const decisionsMutation = useMutation({
    mutationFn: (text) => api.post('/ai/meetings/decisions/', { transcript: text }),
    onSuccess: (res) => handleSuccess('Key Decisions', res.data)
  });

  const emailMutation = useMutation({
    mutationFn: (text) => api.post('/ai/meetings/follow-up-email/', { 
        meeting_summary: text,
        attendees: ["team@example.com"],
        sender: "Project Lead"
    }),
    onSuccess: (res) => handleSuccess('Draft Email', res.data)
  });

  const handleProcess = (type) => {
    if (!notes.trim()) return toast.error('Please enter meeting notes first');
    
    if (type === 'summary') summaryMutation.mutate(notes);
    if (type === 'actions') actionItemsMutation.mutate(notes);
    if (type === 'sentiment') sentimentMutation.mutate(notes);
    if (type === 'decisions') decisionsMutation.mutate(notes);
    if (type === 'email') emailMutation.mutate(notes);
  };

  // --- PARSING HELPER ---
  const parseBold = (text) => {
    if (!text) return null;
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index} className={styles.boldText}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  const renderFormattedText = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    
    return (
      <div className={styles.formattedResult}>
        {lines.map((line, index) => {
          const trimmed = line.trim();
          if (!trimmed) return <div key={index} className="h-2" />; // Spacer

          // Headers (### or **)
          if (trimmed.startsWith('###') || (trimmed.startsWith('**') && trimmed.endsWith('**') && trimmed.length < 60)) {
             return (
               <h4 key={index} className={styles.aiHeader}>
                 {trimmed.replace(/###/g, '').replace(/\*\*/g, '').trim()}
               </h4>
             );
          }

          // List Items (* or -)
          if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
            return (
              <div key={index} className={styles.aiListItem}>
                <span className={styles.bullet}>•</span>
                <span>{parseBold(trimmed.substring(2))}</span>
              </div>
            );
          }

          // Regular Paragraph
          return (
             <p key={index} className={styles.aiParagraph}>
                {parseBold(trimmed)}
             </p>
          );
        })}
      </div>
    );
  };

  // --- RENDER LOGIC ---
  const renderOutput = () => {
    if (!result) {
        return <div className={styles.placeholder}>Analysis results will appear here...</div>;
    }

    const { type, content } = result;

    // 1. Action Items (Handling Nested JSON Structure)
    // Sometimes the AI returns { action_items: [ ... ] } inside the content object
    // Or sometimes it's nested deeper: { action_items: { action_items: [ ... ] } }
    let items = [];
    if (Array.isArray(content.action_items)) {
        items = content.action_items;
    } else if (content.action_items?.action_items && Array.isArray(content.action_items.action_items)) {
        items = content.action_items.action_items;
    }

    if (items.length > 0) {
        return (
            <div className={styles.actionList}>
                {items.map((item, i) => (
                    <div key={i} className={styles.actionCard}>
                        <div className={styles.actionCheckbox}>
                            <div className="w-2 h-2 rounded-full bg-blue-500 opacity-0 group-hover:opacity-100" />
                        </div>
                        <div className={styles.actionContent}>
                            <h4>{item.title}</h4>
                            <div className={styles.actionMeta}>
                                {item.assignee && (
                                    <span className={styles.actionTag}>
                                        <User size={12} className="inline mr-1 text-gray-500" />
                                        {item.assignee}
                                    </span>
                                )}
                                {item.due_date && (
                                    <span className={styles.actionTag}>
                                        <Calendar size={12} className="inline mr-1 text-gray-500" />
                                        {item.due_date}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    // 2. Summary or Decisions (Text Field)
    if (content.summary || content.decisions) {
        return renderFormattedText(content.summary || content.decisions);
    }

    // 3. Draft Email (Text Field)
    if (content.email) {
        return renderFormattedText(content.email);
    }

    // 4. Sentiment (Text or structured)
    if (content.sentiment) {
        const text = content.sentiment;
        let sentimentClass = '';
        if (text.toLowerCase().includes('positive')) sentimentClass = styles.sentimentPositive;
        else if (text.toLowerCase().includes('negative')) sentimentClass = styles.sentimentNegative;

        return (
            <div className={styles.sentimentCard}>
                <div className={`${styles.sentimentIcon} ${sentimentClass}`}>
                    <BarChart size={24} />
                </div>
                <h4 className={styles.sentimentTitle}>Sentiment Analysis</h4>
                <p className={styles.sentimentBody}>{text}</p>
            </div>
        );
    }

    // Default Fallback
    return <pre className={styles.rawJson}>{JSON.stringify(content, null, 2)}</pre>;
  };

  return (
    <div className={styles.container}>
      {/* Input Section */}
      <div className={styles.inputColumn}>
        <h3 className={styles.title}>Input Meeting Notes</h3>
        <textarea
          className={styles.textArea}
          placeholder="Paste transcript or notes here..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
        <div className={styles.actions}>
           <Button onClick={() => handleProcess('summary')} isLoading={summaryMutation.isPending} disabled={!notes} className="flex-1">
             <FileText size={16} className="mr-2" /> Summarize
           </Button>
           <Button variant="ghost" onClick={() => handleProcess('actions')} isLoading={actionItemsMutation.isPending} disabled={!notes}>
             <List size={16} className="mr-2" /> Action Items
           </Button>
           <Button variant="ghost" onClick={() => handleProcess('sentiment')} isLoading={sentimentMutation.isPending} disabled={!notes}>
             <BarChart size={16} className="mr-2" /> Sentiment
           </Button>
           <Button variant="ghost" onClick={() => handleProcess('decisions')} isLoading={decisionsMutation.isPending} disabled={!notes}>
             <CheckCircle size={16} className="mr-2" /> Decisions
           </Button>
           <Button variant="ghost" onClick={() => handleProcess('email')} isLoading={emailMutation.isPending} disabled={!notes}>
             <Mail size={16} className="mr-2" /> Draft Email
           </Button>
        </div>
      </div>

      {/* Output Section */}
      <div className={styles.outputColumn}>
        <div className={styles.outputHeader}>
           <h3 className={styles.title}>{result ? result.type : 'AI Output'}</h3>
           {result && (
             <button 
                className={styles.copyBtn}
                onClick={() => { 
                    const text = typeof result.content === 'object' ? JSON.stringify(result.content, null, 2) : Object.values(result.content)[0];
                    navigator.clipboard.writeText(text); 
                    toast.success('Copied'); 
                }}
             >
                <Copy size={18} />
             </button>
           )}
        </div>
        
        <div className={styles.outputContent}>
           {renderOutput()}
        </div>
      </div>
    </div>
  );
};

export default AIMeetingProcessor;