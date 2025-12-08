import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { FileText, List, BarChart, Copy } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Button from '../../components/ui/Button/Button';
import styles from './AIMeetingProcessor.module.css';

const AIMeetingProcessor = () => {
  const [notes, setNotes] = useState('');
  const [result, setResult] = useState(null);
  
  // FIX: Updated payload key to 'transcript'
  const summaryMutation = useMutation({
    mutationFn: (text) => api.post('/ai/meetings/summarize/', { 
      transcript: text,
      participants: ["User"], 
      duration: 60 
    }),
    onSuccess: (res) => setResult({ type: 'Summary', content: res.data }),
    onError: (err) => {
        console.error(err);
        toast.error('Failed to generate summary');
    }
  });

  const actionItemsMutation = useMutation({
    mutationFn: (text) => api.post('/ai/meetings/action-items/', { transcript: text }),
    onSuccess: (res) => setResult({ type: 'Action Items', content: res.data }),
    onError: () => toast.error('Failed to extract actions')
  });

  const sentimentMutation = useMutation({
    mutationFn: (text) => api.post('/ai/meetings/sentiment/', { transcript: text }),
    onSuccess: (res) => setResult({ type: 'Sentiment', content: res.data }),
    onError: () => toast.error('Failed to analyze sentiment')
  });

  const handleProcess = (type) => {
    if (!notes.trim()) return toast.error('Please enter meeting notes first');
    if (type === 'summary') summaryMutation.mutate(notes);
    if (type === 'actions') actionItemsMutation.mutate(notes);
    if (type === 'sentiment') sentimentMutation.mutate(notes);
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
           <Button onClick={() => handleProcess('summary')} isLoading={summaryMutation.isPending}>
             <FileText size={16} style={{ marginRight: '0.5rem' }} /> Summarize
           </Button>
           <Button variant="ghost" onClick={() => handleProcess('actions')} isLoading={actionItemsMutation.isPending}>
             <List size={16} style={{ marginRight: '0.5rem' }} /> Action Items
           </Button>
           <Button variant="ghost" onClick={() => handleProcess('sentiment')} isLoading={sentimentMutation.isPending}>
             <BarChart size={16} style={{ marginRight: '0.5rem' }} /> Sentiment
           </Button>
        </div>
      </div>

      {/* Output Section */}
      <div className={styles.outputColumn}>
        <div className={styles.outputHeader}>
           <h3 className={styles.title}>
             {result ? result.type : 'AI Output'}
           </h3>
           {result && (
             <button 
                className={styles.copyBtn}
                onClick={() => { navigator.clipboard.writeText(JSON.stringify(result.content, null, 2)); toast.success('Copied'); }}
             >
                <Copy size={18} />
             </button>
           )}
        </div>
        
        <div className={styles.outputContent}>
           {result ? (
             <pre className={styles.whitespacePreWrap}>{JSON.stringify(result.content, null, 2)}</pre>
           ) : (
             <div className={styles.placeholder}>
                Results will appear here...
             </div>
           )}
        </div>
      </div>
    </div>
  );
};

export default AIMeetingProcessor;