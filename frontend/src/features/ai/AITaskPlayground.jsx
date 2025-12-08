import React, { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { 
  Zap, Clock, ListChecks, Layers, Play, Users, BarChart3, X
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import Button from '../../components/ui/Button/Button';
import Input from '../../components/ui/Input/Input';
import styles from './AITaskPlayground.module.css';

const AITaskPlayground = () => {
  const { currentWorkspace } = useWorkspace();
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [selectedTaskId, setSelectedTaskId] = useState('');
  
  // Inputs
  const [generatePrompt, setGeneratePrompt] = useState('');
  const [analysisText, setAnalysisText] = useState(''); 
  
  // Output State (Replaces Console Log)
  const [result, setResult] = useState(null);
  const [isError, setIsError] = useState(false);

  // --- DATA FETCHING ---

  const { data: projects } = useQuery({
    queryKey: ['workspaceProjects', currentWorkspace?.id],
    queryFn: async () => {
      if (!currentWorkspace?.id) return [];
      const res = await api.get(`/projects/?workspace=${currentWorkspace.id}`);
      return Array.isArray(res.data) ? res.data : (res.data.results || []);
    },
    enabled: !!currentWorkspace?.id
  });

  const { data: tasks } = useQuery({
    queryKey: ['workspaceTasks', selectedProjectId],
    queryFn: async () => {
      const url = selectedProjectId 
        ? `/tasks/tasks/?project=${selectedProjectId}` 
        : `/tasks/tasks/?workspace=${currentWorkspace?.id}`;
      
      try {
        const res = await api.get(url);
        return Array.isArray(res.data) ? res.data : (res.data.results || []);
      } catch { return []; }
    },
    enabled: !!currentWorkspace?.id
  });

  const { data: members } = useQuery({
    queryKey: ['workspaceMembers', currentWorkspace?.id],
    queryFn: async () => {
        if (!currentWorkspace?.id) return [];
        try {
            const res = await api.get(`/workspaces/${currentWorkspace.id}/members/`);
            const list = Array.isArray(res.data) ? res.data : (res.data.results || []);
            
            // FIX: Return full objects with ID, Username, Email for the AI context
            // Backend expects "dictionary of items", not strings
            return list.map(m => ({
                id: m.user?.id || m.id,
                username: m.username || m.user?.username || 'Unknown',
                email: m.email || m.user?.email || ''
            }));
        } catch { return []; }
    },
    enabled: !!currentWorkspace?.id
  });

  // --- AUTO-FILL ---
  useEffect(() => {
    if (selectedTaskId && tasks) {
        const task = tasks.find(t => String(t.id) === String(selectedTaskId));
        if (task) {
            setAnalysisText(task.description || task.title || '');
            setResult(null); // Clear previous results on switch
        }
    }
  }, [selectedTaskId, tasks]);

  // --- HELPER ---
  const handleSuccess = (data) => {
    setResult(data);
    setIsError(false);
    toast.success('AI operation complete');
  };

  const handleError = (error) => {
    setResult(error.response?.data || { error: error.message });
    setIsError(true);
    toast.error('AI operation failed');
  };

  // --- MUTATIONS ---

  const autoCreateMutation = useMutation({
    mutationFn: () => {
       if (!currentWorkspace?.id) throw new Error("No workspace detected.");
       return api.post('/ai/tasks/auto-create/', { 
         text: generatePrompt, 
         workspace_id: currentWorkspace.id,
         project_id: selectedProjectId || undefined 
       });
    },
    onSuccess: (res) => {
       handleSuccess(res.data);
       setGeneratePrompt('');
    },
    onError: handleError
  });

  const breakdownMutation = useMutation({
    mutationFn: () => api.post('/ai/tasks/breakdown/', { 
        task_description: analysisText // FIX: Send description to avoid UUID error
    }),
    onSuccess: (res) => handleSuccess(res.data),
    onError: handleError
  });

  const estimateMutation = useMutation({
    mutationFn: () => api.post('/ai/tasks/estimate/', { 
        task_description: analysisText 
    }),
    onSuccess: (res) => handleSuccess(res.data),
    onError: handleError
  });

  const priorityMutation = useMutation({
    mutationFn: () => api.post('/ai/tasks/priority/', { 
        task_description: analysisText 
    }),
    onSuccess: (res) => handleSuccess(res.data),
    onError: handleError
  });

  const assigneeMutation = useMutation({
    mutationFn: () => {
        if (!members || members.length === 0) throw new Error("No team members found in workspace.");
        
        return api.post('/ai/tasks/suggest-assignee/', { 
            task_description: analysisText, // FIX: Send description
            team_members: members // FIX: Sending array of objects
        });
    },
    onSuccess: (res) => handleSuccess(res.data),
    onError: handleError
  });

  return (
    <div className={styles.container}>
      <div className={styles.contentWrapper}>
         
         {/* --- GENERATOR --- */}
         <div className={styles.card}>
            <div className={styles.header}>
               <div className={`${styles.iconWrapper} ${styles.iconYellow}`}>
                  <Zap size={20} />
               </div>
               <h3 className={styles.title}>Task Generator</h3>
            </div>

            <div className={styles.inputGroup}>
               <label className={styles.label}>Target Project (Optional)</label>
               <select 
                  className={styles.select}
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
               >
                  <option value="" disabled>Select a Project</option>
                  {projects?.map(p => (
                     <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
               </select>
            </div>

            <div className={styles.inputGroup}>
               <label className={styles.label}>Requirement / Prompt</label>
               <textarea 
                  className={styles.textArea}
                  placeholder="e.g. 'Create a user registration flow with email verification and OAuth support'"
                  value={generatePrompt}
                  onChange={(e) => setGeneratePrompt(e.target.value)}
               />
            </div>

            <Button 
              onClick={() => autoCreateMutation.mutate()} 
              isLoading={autoCreateMutation.isPending}
              disabled={!generatePrompt}
              className="w-full"
            >
               <Play size={16} style={{marginRight:'8px'}} /> Auto-Create Tasks
            </Button>
         </div>

         {/* --- ANALYZER --- */}
         <div className={styles.card}>
            <div className={styles.header}>
               <div className={`${styles.iconWrapper} ${styles.iconBlue}`}>
                  <Layers size={20} />
               </div>
               <h3 className={styles.title}>Task Intelligence</h3>
            </div>
            
            <div className={styles.inputGroup}>
               <label className={styles.label}>Select Task to Analyze</label>
               <select 
                    className={styles.select}
                    value={selectedTaskId}
                    onChange={(e) => setSelectedTaskId(e.target.value)}
                >
                    <option value="" disabled>Choose a task...</option>
                    {tasks?.map(t => (
                        <option key={t.id} value={t.id}>{t.title}</option>
                    ))}
                </select>
                {(!tasks || tasks.length === 0) && (
                    <p style={{fontSize:'0.75rem', color:'#94a3b8', marginTop:'0.5rem'}}>
                       No tasks found. Create one above to analyze.
                    </p>
                )}
            </div>

            <div className={styles.inputGroup}>
               <label className={styles.label}>Analysis Content</label>
               <textarea
                 className={styles.textArea}
                 rows={4}
                 placeholder="Auto-filled from task description, or type here to analyze raw text..."
                 value={analysisText}
                 onChange={(e) => setAnalysisText(e.target.value)}
               />
            </div>

            <div className={styles.actionsGrid}>
               <Button 
                 variant="outline" 
                 onClick={() => breakdownMutation.mutate()} 
                 disabled={!analysisText} 
                 isLoading={breakdownMutation.isPending}
                 className="justify-center text-sm"
               >
                  <ListChecks size={14} className="mr-1" /> Breakdown
               </Button>
               
               <Button 
                 variant="outline" 
                 onClick={() => assigneeMutation.mutate()} 
                 disabled={!analysisText} 
                 isLoading={assigneeMutation.isPending}
                 className="justify-center text-sm"
               >
                  <Users size={14} className="mr-1" /> Assignee
               </Button>

               <Button 
                 variant="outline" 
                 onClick={() => estimateMutation.mutate()} 
                 disabled={!analysisText} 
                 isLoading={estimateMutation.isPending}
                 className="justify-center text-sm"
               >
                  <Clock size={14} className="mr-1" /> Estimate
               </Button>

               <Button 
                 variant="outline" 
                 onClick={() => priorityMutation.mutate()} 
                 disabled={!analysisText} 
                 isLoading={priorityMutation.isPending}
                 className="justify-center text-sm"
               >
                  <BarChart3 size={14} className="mr-1" /> Priority
               </Button>
            </div>
         </div>

         {/* --- RESULT OUTPUT --- */}
         {result && (
            <div className={`${styles.resultBox} ${isError ? styles.errorBox : ''}`}>
               <div className={styles.resultHeader}>
                  <span>AI Response</span>
                  <button onClick={() => setResult(null)} className="text-gray-400 hover:text-gray-600">
                     <X size={16} />
                  </button>
               </div>
               <pre className={styles.jsonOutput}>{JSON.stringify(result, null, 2)}</pre>
            </div>
         )}
      </div>
    </div>
  );
};

export default AITaskPlayground;