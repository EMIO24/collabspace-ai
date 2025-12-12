import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Code2, Terminal, Play, Bug, BookOpen, RefreshCw, Copy, ShieldCheck, X } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Button from '../../components/ui/Button/Button';
import styles from './AICodeAssistant.module.css';

const LANGUAGES = ['python', 'javascript', 'typescript', 'java', 'cpp', 'go', 'html', 'css', 'sql'];

const AICodeAssistant = () => {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [result, setResult] = useState(null);
  const [isError, setIsError] = useState(false);
  const [errorMsg, setErrorMsg] = useState(''); // For Debug mode

  // --- HELPERS ---
  const handleSuccess = (type, content) => {
    setResult({ type, content });
    setIsError(false);
    toast.success(`${type} complete`);
  };

  const handleError = (error) => {
    setResult({ type: 'Error', content: error.response?.data?.message || error.message });
    setIsError(true);
    toast.error('Operation failed');
  };

  const copyResult = () => {
    if (result?.content) {
        navigator.clipboard.writeText(result.content);
        toast.success('Copied to clipboard');
    }
  };

  // --- MUTATIONS ---
  const reviewMutation = useMutation({
    mutationFn: () => api.post('/ai/code/review/', { code, language }),
    onSuccess: (res) => handleSuccess('Code Review', res.data.review),
    onError: handleError
  });

  const explainMutation = useMutation({
    mutationFn: () => api.post('/ai/code/explain/', { code, language }),
    onSuccess: (res) => handleSuccess('Explanation', res.data.explanation),
    onError: handleError
  });

  const debugMutation = useMutation({
    mutationFn: () => api.post('/ai/code/debug/', { code, error_message: errorMsg || 'Unknown error' }),
    onSuccess: (res) => handleSuccess('Debug Solution', res.data.debug_solution),
    onError: handleError
  });

  const testsMutation = useMutation({
    mutationFn: () => api.post('/ai/code/tests/', { code, language }),
    onSuccess: (res) => handleSuccess('Unit Tests', res.data.tests),
    onError: handleError
  });

  const refactorMutation = useMutation({
    mutationFn: () => api.post('/ai/code/refactor/', { code, language, refactor_goal: 'improve readability and performance' }),
    onSuccess: (res) => handleSuccess('Refactored Code', res.data.refactored_code),
    onError: handleError
  });

  return (
    <div className={styles.container}>
      {/* Left Column: Input Form */}
      <div className={styles.column}>
        <div className={styles.card}>
           <div className={styles.header}>
              <div className={styles.iconWrapper}><Code2 size={20} /></div>
              <h3 style={{margin:0, color:'#1e293b'}}>Code Input</h3>
           </div>
           
           <div>
              <label className={styles.label}>Language</label>
              <select className={styles.select} value={language} onChange={(e) => setLanguage(e.target.value)}>
                 {LANGUAGES.map(lang => <option key={lang} value={lang}>{lang.toUpperCase()}</option>)}
              </select>
           </div>

           <div>
              <label className={styles.label}>Source Code</label>
              <textarea
                  className={styles.codeEditor}
                  placeholder="// Paste your code here..."
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  spellCheck="false"
              />
           </div>
           
           <div>
              <label className={styles.label}>Error Message (For Debugging)</label>
              <input 
                  className={styles.textInput}
                  placeholder="Optional: Paste error message..."
                  value={errorMsg}
                  onChange={(e) => setErrorMsg(e.target.value)}
              />
           </div>
        </div>

        <div className={styles.actionGrid}>
           <Button onClick={() => reviewMutation.mutate()} isLoading={reviewMutation.isPending} disabled={!code}>
              <ShieldCheck size={16} className="mr-2" /> Review
           </Button>
           <Button variant="outline" onClick={() => explainMutation.mutate()} isLoading={explainMutation.isPending} disabled={!code}>
              <BookOpen size={16} className="mr-2" /> Explain
           </Button>
           <Button variant="outline" onClick={() => debugMutation.mutate()} isLoading={debugMutation.isPending} disabled={!code}>
              <Bug size={16} className="mr-2" /> Debug
           </Button>
           <Button variant="outline" onClick={() => testsMutation.mutate()} isLoading={testsMutation.isPending} disabled={!code}>
              <Play size={16} className="mr-2" /> Tests
           </Button>
           <Button variant="outline" onClick={() => refactorMutation.mutate()} isLoading={refactorMutation.isPending} disabled={!code}>
              <RefreshCw size={16} className="mr-2" /> Refactor
           </Button>
        </div>
      </div>

      {/* Right Column: Output Result */}
      <div className={styles.column}>
         {result ? (
            <div className={`${styles.resultBox} ${isError ? styles.errorBox : ''}`}>
               <div className={styles.resultHeader}>
                  <span>{result.type}</span>
                  <div style={{display:'flex', gap:'0.5rem'}}>
                      <button className={styles.copyBtn} onClick={copyResult} title="Copy Output">
                          <Copy size={16} />
                      </button>
                      <button className={styles.copyBtn} onClick={() => setResult(null)}>
                          <X size={16} />
                      </button>
                  </div>
               </div>
               <div className={styles.resultContent}>
                  {/* If it's code, wrap in pre tag, otherwise standard div */}
                  <pre className={styles.codeBlock}>{result.content}</pre>
               </div>
            </div>
         ) : (
            <div className={styles.placeholder}>
               // AI response will appear here...<br/>
               // Select an action to process your code.
            </div>
         )}
      </div>
    </div>
  );
};

export default AICodeAssistant;