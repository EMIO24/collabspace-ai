import React, { useState, useEffect, useMemo } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { 
  Zap, Clock, ListChecks, Layers, Terminal, 
  Play, Users, BarChart3, RotateCcw, Copy, X
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import Button from '../../components/ui/Button/Button';
import Input from '../../components/ui/Input/Input';
import AssigneeSkillsModal from './AssigneeSkillsModal';
import styles from './AITaskPlayground.module.css';

const AITaskPlayground = () => {
  const { currentWorkspace } = useWorkspace();
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [selectedTaskId, setSelectedTaskId] = useState('');
  
  // Inputs
  const [generatePrompt, setGeneratePrompt] = useState('');
  const [analysisText, setAnalysisText] = useState(''); 
  
  // Output State
  const [result, setResult] = useState(null);
  const [isError, setIsError] = useState(false);
  const [isAssigneeModalOpen, setIsAssigneeModalOpen] = useState(false);

  // --- DATA FETCHING ---

  // 1. Projects (Normalized)
  const { data: rawProjects } = useQuery({
    queryKey: ['workspaceProjects', currentWorkspace?.id],
    queryFn: async () => {
      if (!currentWorkspace?.id) return [];
      try {
        const res = await api.get(`/projects/?workspace=${currentWorkspace.id}`);
        return res.data;
      } catch { return []; }
    },
    enabled: !!currentWorkspace?.id
  });

  const projects = useMemo(() => {
    if (!rawProjects) return [];
    if (Array.isArray(rawProjects)) return rawProjects;
    if (rawProjects.results && Array.isArray(rawProjects.results)) return rawProjects.results;
    return [];
  }, [rawProjects]);

  // 2. Tasks (Normalized)
  const { data: rawTasks } = useQuery({
    queryKey: ['workspaceTasks', selectedProjectId],
    queryFn: async () => {
      const url = selectedProjectId 
        ? `/tasks/tasks/?project=${selectedProjectId}` 
        : `/tasks/tasks/?workspace=${currentWorkspace?.id}`;
      
      try {
        const res = await api.get(url);
        return res.data;
      } catch { return []; }
    },
    enabled: !!currentWorkspace?.id
  });

  const tasks = useMemo(() => {
    if (!rawTasks) return [];
    if (Array.isArray(rawTasks)) return rawTasks;
    if (rawTasks.results && Array.isArray(rawTasks.results)) return rawTasks.results;
    return [];
  }, [rawTasks]);

  // 3. Members (Normalized)
  const { data: rawMembers } = useQuery({
    queryKey: ['workspaceMembers', currentWorkspace?.id],
    queryFn: async () => {
        if (!currentWorkspace?.id) return [];
        try {
            const res = await api.get(`/workspaces/${currentWorkspace.id}/members/`);
            return res.data;
        } catch { return []; }
    },
    enabled: !!currentWorkspace?.id
  });

  const members = useMemo(() => {
      let list = [];
      if (Array.isArray(rawMembers)) list = rawMembers;
      else if (rawMembers?.results && Array.isArray(rawMembers.results)) list = rawMembers.results;

      // Map to safe object structure
      return list.map(m => ({
          id: m.user?.id || m.id,
          username: m.username || m.user?.username || 'Unknown',
          email: m.email || m.user?.email || '',
          avatar: m.avatar || m.user?.avatar
      }));
  }, [rawMembers]);

  // --- AUTO-FILL ---
  useEffect(() => {
    if (selectedTaskId && tasks.length > 0) {
        const task = tasks.find(t => String(t.id) === String(selectedTaskId));
        if (task) {
            setAnalysisText(task.description || task.title || '');
            setResult(null); 
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
    mutationFn: () => api.post('/ai/tasks/breakdown/', { task_description: analysisText }),
    onSuccess: (res) => handleSuccess(res.data),
    onError: handleError
  });

  const estimateMutation = useMutation({
    mutationFn: () => api.post('/ai/tasks/estimate/', { task_description: analysisText }),
    onSuccess: (res) => handleSuccess(res.data),
    onError: handleError
  });

  const priorityMutation = useMutation({
    mutationFn: () => api.post('/ai/tasks/priority/', { task_description: analysisText }),
    onSuccess: (res) => handleSuccess(res.data),
    onError: handleError
  });

  const assigneeMutation = useMutation({
    mutationFn: (enrichedMembers) => {
        return api.post('/ai/tasks/suggest-assignee/', { 
            task_description: analysisText, 
            team_members: enrichedMembers 
        });
    },
    onSuccess: (res) => {
       handleSuccess(res.data);
       setIsAssigneeModalOpen(false);
    },
    onError: handleError
  });

  // --- RENDER HELPERS ---
  const renderResult = () => {
    if (!result) return null;

    // 1. Task Breakdown / Lists
    const taskList = result.subtasks || result.created_tasks || result.suggested_tasks;

    if (taskList) {
        if (typeof taskList === 'string') {
            return <div className={styles.resultText}>{taskList}</div>;
        }
        if (Array.isArray(taskList)) {
            return (
                <div className={styles.taskList}>
                    {taskList.map((task, i) => (
                        <div key={i} className={styles.taskCard}>
                            <div className={styles.taskHeader}>
                                <h4 className={styles.taskTitle}>
                                   <span className={styles.taskNumber}>{i + 1}</span>
                                   {task.title}
                                </h4>
                                {task.estimated_hours && (
                                    <span className={styles.taskTag}>
                                        {task.estimated_hours}h
                                    </span>
                                )}
                            </div>
                            <p className={styles.taskDesc}>{task.description}</p>
                        </div>
                    ))}
                </div>
            );
        }
    }

    // 2. Estimate
    if (result.estimate) {
        return (
            <div className={styles.simpleResult}>
                 <Clock size={32} className="text-blue-500 mb-2 mx-auto" />
                 <h3 className={styles.simpleTitle}>Estimate</h3>
                 <p className={styles.simpleText}>{result.estimate}</p>
            </div>
        );
    }

    // 3. Priority
    if (result.priority) {
        return (
            <div className={styles.simpleResult}>
                 <BarChart3 size={32} className="text-purple-500 mb-2 mx-auto" />
                 <h3 className={styles.simpleTitle}>{result.priority}</h3>
                 <p className={styles.simpleText}>Recommended Priority</p>
            </div>
        );
    }
    
    // 4. Assignee
    if (result.assignee) {
        return (
            <div className={styles.assigneeCard}>
                 <div className={styles.assigneeIcon}>
                    <Users size={24} />
                 </div>
                 <div className={styles.assigneeInfo}>
                    <h3>Suggested Assignee</h3>
                    <p className={styles.assigneeName}>{result.assignee}</p>
                 </div>
            </div>
        );
    }

    // Default Fallback
    return <pre className={styles.jsonOutput}>{JSON.stringify(result, null, 2)}</pre>;
  };

  return (
    <div className={styles.container}>
      <div className={styles.contentWrapper}>
         
         {/* Generator Section */}
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
                  <option value="">No specific project</option>
                  {projects.map(p => (
                     <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
               </select>
            </div>

            <div className={styles.inputGroup}>
               <label className={styles.label}>Requirement / Prompt</label>
               <textarea 
                  className={styles.textArea}
                  rows={3}
                  placeholder="Describe a feature..."
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

         {/* Analyzer Section */}
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
                    {tasks.map(t => (
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
                 placeholder="Auto-filled from task description..."
                 value={analysisText}
                 onChange={(e) => setAnalysisText(e.target.value)}
               />
            </div>

            <div className={styles.actionsGrid}>
               <Button variant="outline" onClick={() => breakdownMutation.mutate()} disabled={!analysisText} isLoading={breakdownMutation.isPending} className="justify-center text-sm">
                  <ListChecks size={14} className="mr-1" /> Breakdown
               </Button>
               
               <Button variant="outline" onClick={() => setIsAssigneeModalOpen(true)} disabled={!analysisText} isLoading={assigneeMutation.isPending} className="justify-center text-sm">
                  <Users size={14} className="mr-1" /> Assignee
               </Button>

               <Button variant="outline" onClick={() => estimateMutation.mutate()} disabled={!analysisText} isLoading={estimateMutation.isPending} className="justify-center text-sm">
                  <Clock size={14} className="mr-1" /> Estimate
               </Button>

               <Button variant="outline" onClick={() => priorityMutation.mutate()} disabled={!analysisText} isLoading={priorityMutation.isPending} className="justify-center text-sm">
                  <BarChart3 size={14} className="mr-1" /> Priority
               </Button>
            </div>
         </div>

         {/* Result Output */}
         {result && (
            <div className={`${styles.resultBox} ${isError ? styles.errorBox : ''}`}>
               <div className={styles.resultHeader}>
                  <span>AI Response</span>
                  <button onClick={() => setResult(null)} className="text-gray-400 hover:text-gray-600">
                     <X size={16} />
                  </button>
               </div>
               {renderResult()}
            </div>
         )}
      </div>

      {isAssigneeModalOpen && (
         <AssigneeSkillsModal 
            members={members || []}
            onClose={() => setIsAssigneeModalOpen(false)}
            isLoading={assigneeMutation.isPending}
            onConfirm={(enrichedMembers) => assigneeMutation.mutate(enrichedMembers)}
         />
      )}
    </div>
  );
};

export default AITaskPlayground;