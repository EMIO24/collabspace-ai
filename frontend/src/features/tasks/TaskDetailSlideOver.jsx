import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, Star, MoreHorizontal, Trash2, Send, Play, Square, 
  Copy, ArrowRight, Plus, Check, UploadCloud, FileText, 
  Download, Clock, Calendar, User, Tag, Activity, Smile, Paperclip, Bold, Italic, Link as LinkIcon
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import Avatar from '../../components/ui/Avatar/Avatar';
import Button from '../../components/ui/Button/Button';
import styles from './TaskDetailSlideOver.module.css';

const TABS = {
  COMMENTS: 'Comments',
  ATTACHMENTS: 'Attachments',
  TIME: 'Time Tracking',
  ACTIVITY: 'Activity'
};

const TaskDetailSlideOver = ({ taskId, onClose }) => {
  const { currentWorkspace } = useWorkspace();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState(TABS.COMMENTS);
  const [taskData, setTaskData] = useState(null);
  
  // Input States
  const [commentText, setCommentText] = useState('');
  const [newSubtask, setNewSubtask] = useState('');
  const [newLabel, setNewLabel] = useState('');
  const fileInputRef = useRef(null);

  // Time Tracking State
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const timerRef = useRef(null);
  
  // Manual Time Entry State
  const [manualTime, setManualTime] = useState({ 
    date: new Date().toISOString().split('T')[0], 
    hours: '', 
    description: '' 
  });

  // Move Project State
  const [isMoving, setIsMoving] = useState(false);

  const safeId = taskId ? String(taskId) : '';

  // --- QUERIES ---

  const { data: task } = useQuery({
    queryKey: ['task', taskId],
    queryFn: async () => (await api.get(`/tasks/tasks/${taskId}/`)).data,
    enabled: !!taskId
  });

  const { data: rawProjectLabels } = useQuery({
    queryKey: ['projectLabels', task?.project],
    queryFn: async () => {
        if (!task?.project) return [];
        try {
            const res = await api.get(`/projects/${task.project}/labels/`);
            return res.data;
        } catch { return []; }
    },
    enabled: !!task?.project
  });

  const { data: subtasksList } = useQuery({
    queryKey: ['subtasks', taskId],
    queryFn: async () => {
      try {
          const res = await api.get(`/tasks/tasks/?parent_task=${taskId}`);
          return res.data;
      } catch { return []; }
    },
    enabled: !!taskId
  });

  const { data: rawComments } = useQuery({
    queryKey: ['taskComments', taskId],
    queryFn: async () => (await api.get(`/tasks/comments/?task=${taskId}`)).data || [],
    enabled: !!taskId && activeTab === TABS.COMMENTS
  });

  const { data: files } = useQuery({
    queryKey: ['taskFiles', taskId],
    queryFn: async () => {
        try {
            const res = await api.get(`/files/?task=${taskId}`);
            return Array.isArray(res.data) ? res.data : (res.data.results || []);
        } catch { return []; }
    },
    enabled: !!taskId && activeTab === TABS.ATTACHMENTS
  });

  const { data: rawTimeEntries } = useQuery({
    queryKey: ['taskTime', taskId],
    queryFn: async () => (await api.get(`/tasks/time-entries/?task=${taskId}`)).data || [],
    enabled: !!taskId && activeTab === TABS.TIME
  });

  const { data: activityLog } = useQuery({
    queryKey: ['taskActivity', taskId],
    queryFn: async () => {
         try {
             return [
                 { id: 1, action: 'created', user: task?.created_by, created_at: task?.created_at },
                 { id: 2, action: 'updated status', user: task?.assigned_to, created_at: task?.updated_at }
             ];
         } catch { return []; }
    },
    enabled: !!taskId && activeTab === TABS.ACTIVITY
  });

  const { data: projects } = useQuery({
    queryKey: ['projects', currentWorkspace?.id],
    queryFn: async () => (await api.get(`/projects/?workspace=${currentWorkspace.id}`)).data || [],
    enabled: !!currentWorkspace
  });

  const { data: members } = useQuery({
    queryKey: ['workspaceMembers', currentWorkspace?.id],
    queryFn: async () => (await api.get(`/workspaces/${currentWorkspace.id}/members/`)).data || [],
    enabled: !!currentWorkspace
  });

  // --- DATA NORMALIZATION (Prevents crashes) ---

  const projectLabels = useMemo(() => {
    if (!rawProjectLabels) return [];
    if (Array.isArray(rawProjectLabels)) return rawProjectLabels;
    if (rawProjectLabels.results && Array.isArray(rawProjectLabels.results)) return rawProjectLabels.results;
    return [];
  }, [rawProjectLabels]);

  const comments = useMemo(() => {
    if (!rawComments) return [];
    if (Array.isArray(rawComments)) return rawComments;
    return rawComments.results || [];
  }, [rawComments]);

  const timeEntries = useMemo(() => {
    if (!rawTimeEntries) return [];
    if (Array.isArray(rawTimeEntries)) return rawTimeEntries;
    if (rawTimeEntries.results && Array.isArray(rawTimeEntries.results)) return rawTimeEntries.results;
    return [];
  }, [rawTimeEntries]);

  // Merge subtasks from separate API call or embedded task object
  const displayedSubtasks = useMemo(() => {
      let list = [];
      if (Array.isArray(subtasksList)) list = subtasksList;
      else if (subtasksList?.results) list = subtasksList.results;
      else if (task?.subtasks && Array.isArray(task.subtasks)) list = task.subtasks;
      return list;
  }, [subtasksList, task]);

  useEffect(() => {
    if (task) {
        setTaskData({
            ...task,
            subtasks: task.subtasks || [],
            tags: task.tags || []
        });
    }
  }, [task]);

  // --- MUTATIONS ---
  const updateMutation = useMutation({
    mutationFn: (updates) => api.patch(`/tasks/tasks/${taskId}/`, updates),
    onSuccess: () => {
       queryClient.invalidateQueries(['task', taskId]);
       queryClient.invalidateQueries(['tasks']);
    }
  });

  const assignMutation = useMutation({
    mutationFn: (userId) => api.post(`/tasks/tasks/${taskId}/assign_task/`, { user_id: userId }),
    onSuccess: () => {
        queryClient.invalidateQueries(['task', taskId]);
        toast.success('Assignee updated');
    },
    onError: (e) => toast.error('Assignment failed')
  });

  const commentMutation = useMutation({
    mutationFn: (text) => api.post('/tasks/comments/', { task: taskId, content: text }),
    onSuccess: () => {
       queryClient.invalidateQueries(['taskComments', taskId]);
       setCommentText('');
       toast.success('Comment added');
    }
  });

  const uploadMutation = useMutation({
    mutationFn: (file) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('task', taskId);
        formData.append('name', file.name);
        formData.append('workspace', currentWorkspace.id);
        return api.post('/files/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    },
    onSuccess: () => {
        queryClient.invalidateQueries(['taskFiles', taskId]);
        toast.success('File uploaded');
    },
    onError: () => toast.error('Upload failed')
  });
  
  const deleteFileMutation = useMutation({
      mutationFn: (fileId) => api.delete(`/files/${fileId}/`),
      onSuccess: () => {
          queryClient.invalidateQueries(['taskFiles', taskId]);
          toast.success('File removed');
      }
  });

  const createSubtaskMutation = useMutation({
    mutationFn: (title) => api.post('/tasks/tasks/', {
        title: title,
        parent_task_id: taskId,  
        project: taskData.project, 
        status: 'todo',
        priority: 'medium'
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['subtasks', taskId]); 
      setNewSubtask('');
      toast.success('Subtask added');
    },
    onError: () => {
        // Fallback for when backend doesn't support separate subtask objects
        const updated = [...(taskData.subtasks || []), { title: newSubtask, completed: false, id: Date.now() }];
        setTaskData(prev => ({ ...prev, subtasks: updated }));
        updateMutation.mutate({ subtasks: updated });
        setNewSubtask('');
    }
  });

  const toggleSubtaskMutation = useMutation({
    mutationFn: ({ subtaskId, isCompleted }) => 
        api.patch(`/tasks/tasks/${subtaskId}/`, { status: isCompleted ? 'done' : 'todo' }),
    onSuccess: () => queryClient.invalidateQueries(['subtasks', taskId]),
    onError: () => {
         // Fallback local toggle
         const updated = [...taskData.subtasks];
         const index = updated.findIndex(s => s.id === subtaskId);
         if (index !== -1) {
             updated[index].completed = !updated[index].completed;
             setTaskData(prev => ({ ...prev, subtasks: updated }));
         }
    }
  });

  const timeEntryMutation = useMutation({
    mutationFn: (data) => api.post('/tasks/time-entries/', { task: taskId, ...data }),
    onSuccess: () => {
        queryClient.invalidateQueries(['taskTime', taskId]);
        toast.success('Time logged');
        setManualTime({ date: new Date().toISOString().split('T')[0], hours: '', description: '' });
    },
    onError: (err) => {
        const msg = err.response?.data?.message || 'Failed to log time';
        toast.error(typeof msg === 'object' ? JSON.stringify(msg) : msg);
    }
  });

  const duplicateMutation = useMutation({
    mutationFn: () => api.post('/tasks/tasks/', { ...taskData, id: undefined, title: `${taskData.title} (Copy)`, status: 'todo' }),
    onSuccess: () => { toast.success('Task duplicated'); onClose(); queryClient.invalidateQueries(['tasks']); }
  });
  
  const moveProjectMutation = useMutation({
    mutationFn: (projectId) => api.patch(`/tasks/tasks/${taskId}/`, { project: projectId }),
    onSuccess: () => {
      toast.success('Task moved');
      queryClient.invalidateQueries(['tasks']);
      setIsMoving(false);
      onClose();
    },
    onError: () => toast.error('Failed to move task')
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`/tasks/tasks/${taskId}/`),
    onSuccess: () => { toast.success('Task deleted'); onClose(); queryClient.invalidateQueries(['tasks']); }
  });

  // --- HANDLERS ---
  const handleFieldChange = (field, value) => setTaskData(prev => ({ ...prev, [field]: value }));
  const handleBlur = (field) => updateMutation.mutate({ [field]: taskData[field] });

  const handleAddSubtask = (e) => {
    e.preventDefault();
    if (!newSubtask.trim()) return;
    createSubtaskMutation.mutate(newSubtask);
  };

  const toggleSubtask = (id, isCompleted) => {
    toggleSubtaskMutation.mutate({ subtaskId: id, isCompleted });
  };

  // RESTORED: Label Handlers
  const handleAddLabel = (e) => {
      if (e.key === 'Enter' && newLabel.trim()) {
          const currentTags = taskData.tags || [];
          const updatedTags = [...currentTags, { name: newLabel, color: '#3b82f6' }]; 
          setTaskData(prev => ({ ...prev, tags: updatedTags }));
          
          const getTagNames = (tags) => tags.map(t => (typeof t === 'object' ? t.name : t));
          updateMutation.mutate({ tags: getTagNames(updatedTags) });
          setNewLabel('');
      }
  };

  const handleAddExistingLabel = (labelId) => {
      if (!labelId) return;
      const label = projectLabels.find(l => String(l.id) === String(labelId));
      if (!label) return;

      const currentTags = taskData.tags || [];
      if (currentTags.some(t => (typeof t === 'object' ? t.id === label.id : t === label.name))) return;

      const updatedTags = [...currentTags, label];
      setTaskData(prev => ({ ...prev, tags: updatedTags }));
      
      const getTagNames = (tags) => tags.map(t => (typeof t === 'object' ? t.name : t));
      updateMutation.mutate({ tags: getTagNames(updatedTags) });
      toast.success(`Label added`);
  };

  const handleRemoveLabel = (index) => {
      const currentTags = taskData.tags || [];
      const updatedTags = currentTags.filter((_, i) => i !== index);
      setTaskData(prev => ({ ...prev, tags: updatedTags }));
      
      const getTagNames = (tags) => tags.map(t => (typeof t === 'object' ? t.name : t));
      updateMutation.mutate({ tags: getTagNames(updatedTags) });
  };

  const handleTimerToggle = () => {
    if (isTimerRunning) {
        clearInterval(timerRef.current);
        setIsTimerRunning(false);
        if (timerSeconds > 60) {
            const hoursLogged = (timerSeconds / 3600).toFixed(2);
            timeEntryMutation.mutate({ 
                hours: hoursLogged, 
                description: 'Timer Session',
                date: new Date().toISOString().split('T')[0] 
            });
        }
        setTimerSeconds(0);
    } else {
        setIsTimerRunning(true);
        timerRef.current = setInterval(() => setTimerSeconds(s => s + 1), 1000);
    }
  };
  
  const handleManualTimeSubmit = (e) => {
      e.preventDefault();
      timeEntryMutation.mutate({
          date: manualTime.date,
          hours: parseFloat(manualTime.hours), 
          description: manualTime.description
      });
  };

  const insertFormat = (tag) => setCommentText(prev => prev + tag);

  const formatTimer = (totalSeconds) => {
    const h = Math.floor(totalSeconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((totalSeconds % 3600) / 60).toString().padStart(2, '0');
    const s = (totalSeconds % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  };

  if (!taskData) return null;

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <motion.div 
        className={styles.panel} 
        onClick={e => e.stopPropagation()}
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
      >
        {/* Header */}
        <div className={styles.header}>
           <div className="flex items-center gap-3">
              <span className={styles.taskId}>TASK-{safeId.slice(0,6)}</span>
              <button 
                 className={styles.iconBtn} 
                 onClick={() => updateMutation.mutate({ is_favorite: !taskData.is_favorite })}
              >
                 <Star size={18} className={taskData.is_favorite ? styles.starActive : ''} fill={taskData.is_favorite ? "currentColor" : "none"} />
              </button>
           </div>
           <div className={styles.headerActions}>
              <button className={styles.iconBtn}><MoreHorizontal size={18} /></button>
              <button className={styles.iconBtn} onClick={onClose}><X size={20} /></button>
           </div>
        </div>

        <div className={styles.body}>
           <div className={styles.mainContent}>
              <input 
                className={styles.titleInput}
                value={taskData.title || ''}
                onChange={(e) => handleFieldChange('title', e.target.value)}
                onBlur={() => handleBlur('title')}
                placeholder="Task Title"
              />
              <div className={styles.descriptionWrapper}>
                  <div className={styles.editorToolbar}>
                      <button className={styles.toolBtn} onClick={() => insertFormat('**bold**')}><Bold size={14}/></button>
                      <button className={styles.toolBtn} onClick={() => insertFormat('*italic*')}><Italic size={14}/></button>
                      <button className={styles.toolBtn} onClick={() => insertFormat('[link](url)')}><LinkIcon size={14}/></button>
                  </div>
                  <textarea 
                    className={styles.descriptionEditor}
                    value={taskData.description || ''}
                    onChange={(e) => handleFieldChange('description', e.target.value)}
                    onBlur={() => handleBlur('description')}
                    placeholder="Add a detailed description..."
                  />
              </div>

              <div className={styles.tabsContainer}>
                 <div className={styles.tabsList}>
                    {Object.values(TABS).map(tab => (
                       <button 
                         key={tab} 
                         className={`${styles.tab} ${activeTab === tab ? styles.activeTab : ''}`}
                         onClick={() => setActiveTab(tab)}
                       >
                         {tab}
                       </button>
                    ))}
                 </div>
              </div>

              {/* TAB CONTENT */}
              {activeTab === TABS.COMMENTS && (
                 <div className={styles.commentSection}>
                    <div className={styles.commentInputWrapper}>
                       <textarea 
                          className={styles.commentInput} 
                          placeholder="Write a comment..." 
                          value={commentText}
                          onChange={e => setCommentText(e.target.value)}
                       />
                       <div className={styles.commentToolbar}>
                          <Button size="sm" onClick={() => commentMutation.mutate(commentText)} disabled={!commentText.trim()}>
                             <Send size={14} className="mr-2"/> Comment
                          </Button>
                       </div>
                    </div>
                    <div className={styles.commentList}>
                       {comments.map((c, i) => (
                          <div key={i} className={styles.comment}>
                             <Avatar src={c.user?.avatar} fallback={c.user?.username?.[0]} />
                             <div className={styles.commentContent}>
                                <div className={styles.commentHeader}>
                                   <span className={styles.commentAuthor}>{c.user?.username || 'User'}</span>
                                   <span className={styles.commentTime}>{new Date(c.created_at).toLocaleString()}</span>
                                </div>
                                <div className={styles.commentText}>{c.content}</div>
                             </div>
                          </div>
                       ))}
                    </div>
                 </div>
              )}

              {activeTab === TABS.ATTACHMENTS && (
                 <div>
                    <div className={styles.uploadZone} onClick={() => fileInputRef.current.click()}>
                        <UploadCloud size={32} className="mx-auto mb-2 text-blue-500" />
                        <p className="font-semibold text-gray-700">Click or drag to upload files</p>
                        <input ref={fileInputRef} type="file" hidden onChange={(e) => e.target.files[0] && uploadMutation.mutate(e.target.files[0])} />
                    </div>
                    <div className={styles.attachmentList}>
                       {files?.map((file, i) => (
                         <div key={i} className={styles.attachmentItem}>
                            <FileText size={24} className={styles.fileIcon} />
                            <div className={styles.fileInfo}>
                               <div className={styles.fileName}>{file.name}</div>
                               <div className={styles.fileMeta}>{(file.size / 1024).toFixed(1)} KB</div>
                            </div>
                            <button className={styles.iconBtn} onClick={() => window.open(file.url)}><Download size={16}/></button>
                            <button className={styles.iconBtn} onClick={() => deleteFileMutation.mutate(file.id)}><Trash2 size={16}/></button>
                         </div>
                       ))}
                       {files?.length === 0 && <div className="text-center text-gray-400 italic">No attachments yet.</div>}
                    </div>
                 </div>
              )}

              {activeTab === TABS.TIME && (
                 <div className="flex flex-col gap-4">
                    <div className={styles.timerWidget}>
                       <div>
                          <div className="text-xs font-bold text-blue-600 uppercase">Current Session</div>
                          <div className={styles.timerDisplay}>{formatTimer(timerSeconds)}</div>
                       </div>
                       <Button 
                          onClick={handleTimerToggle} 
                          className={isTimerRunning ? 'bg-red-500 hover:bg-red-600 border-red-600' : 'bg-green-600 hover:bg-green-700 border-green-700'}
                       >
                          {isTimerRunning ? <Square size={16} className="mr-2"/> : <Play size={16} className="mr-2"/>}
                          {isTimerRunning ? 'Stop' : 'Start'}
                       </Button>
                    </div>

                    <form onSubmit={handleManualTimeSubmit} className={styles.manualTimeForm}>
                        <div className={styles.formRow}>
                            <input 
                                type="date" 
                                className={styles.dateInput}
                                value={manualTime.date}
                                onChange={e => setManualTime({...manualTime, date: e.target.value})}
                                required
                            />
                            <input 
                                type="number" 
                                className={styles.textInput}
                                placeholder="Hours (e.g. 1.5)"
                                value={manualTime.hours}
                                onChange={e => setManualTime({...manualTime, hours: e.target.value})}
                                step="0.1"
                                required
                            />
                        </div>
                        <input 
                            className={styles.textInput}
                            placeholder="Description (Optional)"
                            value={manualTime.description}
                            onChange={e => setManualTime({...manualTime, description: e.target.value})}
                        />
                        <Button type="submit" variant="outline" className="w-full">Log Manual Entry</Button>
                    </form>
                    
                    <div className={styles.timeLogList}>
                       {timeEntries.map((entry, i) => (
                          <div key={i} className={styles.timeEntry}>
                             <div className="flex items-center gap-3">
                                <Clock size={16} className="text-gray-400"/>
                                <div>
                                   <div className="text-sm font-bold text-gray-700">{entry.description || 'Logged Time'}</div>
                                   <div className="text-xs text-gray-500">{new Date(entry.created_at).toLocaleDateString()}</div>
                                </div>
                             </div>
                             <div className="font-mono font-bold text-gray-800">{entry.hours || entry.duration}h</div>
                          </div>
                       ))}
                    </div>
                 </div>
              )}
           </div>

           {/* RIGHT SIDEBAR */}
           <div className={styles.sidebar}>
              <div className={styles.sidebarSection}>
                 <label className={styles.propertyLabel}>Status</label>
                 <select 
                    className={styles.select}
                    value={taskData.status}
                    onChange={e => {
                       handleFieldChange('status', e.target.value);
                       updateMutation.mutate({ status: e.target.value });
                    }}
                 >
                    <option value="todo">To Do</option>
                    <option value="in_progress">In Progress</option>
                    <option value="review">In Review</option>
                    <option value="done">Done</option>
                 </select>
              </div>

              <div className={styles.sidebarSection}>
                 <label className={styles.propertyLabel}>Assignee</label>
                 <select 
                    className={styles.select}
                    value={taskData.assigned_to?.id || ""}
                    onChange={e => assignMutation.mutate(e.target.value)}
                 >
                    <option value="">Unassigned</option>
                    {members?.map(m => {
                        const user = m.user || m;
                        return <option key={user.id} value={user.id}>{user.username || user.email}</option>;
                    })}
                 </select>
              </div>

              <div className={styles.sidebarSection}>
                 <label className={styles.propertyLabel}>Priority</label>
                 <select 
                    className={styles.select}
                    value={taskData.priority}
                    onChange={e => {
                       handleFieldChange('priority', e.target.value);
                       updateMutation.mutate({ priority: e.target.value });
                    }}
                 >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                 </select>
              </div>
              
              <div className={styles.sidebarSection}>
                 <label className={styles.propertyLabel}>Labels</label>
                 <div className={styles.labelList}>
                    {taskData.tags?.map((tag, i) => (
                       <div key={i} className={styles.labelChip}>
                          {typeof tag === 'object' ? tag.name : tag} 
                          <X size={12} className={styles.removeLabel} onClick={() => handleRemoveLabel(i)} />
                       </div>
                    ))}
                    
                    <select 
                        className={styles.select} 
                        style={{marginTop: '0.25rem', padding: '0.4rem', fontSize: '0.8rem'}}
                        onChange={(e) => handleAddExistingLabel(e.target.value)}
                        value=""
                    >
                        <option value="" disabled>+ Add Label</option>
                        {projectLabels.map(label => (
                            <option key={label.id} value={label.id}>{label.name}</option>
                        ))}
                    </select>

                    <input 
                       className={styles.addLabelInput} 
                       placeholder="New Label..." 
                       value={newLabel}
                       onChange={e => setNewLabel(e.target.value)}
                       onKeyDown={handleAddLabel}
                    />
                 </div>
              </div>

              <div className={styles.sidebarSection}>
                 <label className={styles.propertyLabel}>Subtasks</label>
                 <div className={styles.subtaskList}>
                    {displayedSubtasks.map(st => (
                       <div key={st.id} className={styles.stepCard}>
                          <input 
                             type="checkbox" 
                             className={styles.stepCheckbox}
                             checked={st.status === 'done' || st.completed}
                             onChange={(e) => toggleSubtask(st.id, e.target.checked)}
                          />
                          <div className={styles.stepContent}>
                              <div className={styles.stepHeader}>
                                  <span className={`${styles.stepTitle} ${(st.status === 'done' || st.completed) ? styles.completedTitle : ''}`}>
                                    {st.title}
                                  </span>
                              </div>
                          </div>
                       </div>
                    ))}
                    <form onSubmit={handleAddSubtask} className={styles.subtaskForm}>
                       <Plus size={16} className="text-gray-400" />
                       <input 
                          className={styles.subtaskInput}
                          placeholder="Add subtask..." 
                          value={newSubtask}
                          onChange={e => setNewSubtask(e.target.value)}
                       />
                    </form>
                 </div>
              </div>

              <div className={styles.sidebarFooter}>
                 <button className={styles.actionRowBtn} onClick={() => duplicateMutation.mutate()}>
                    <Copy size={16} /> Duplicate Task
                 </button>
                 
                 {!isMoving ? (
                    <button className={styles.actionRowBtn} onClick={() => setIsMoving(true)}>
                       <ArrowRight size={16} /> Move to Project
                    </button>
                  ) : (
                    <div className="bg-white p-2 rounded border border-blue-200">
                       <select className={styles.select} onChange={(e) => { if(e.target.value) moveProjectMutation.mutate(e.target.value) }}>
                          <option value="">Choose Project...</option>
                          {projects?.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                       </select>
                       <button className="text-xs text-red-500 mt-1" onClick={() => setIsMoving(false)}>Cancel</button>
                    </div>
                  )}

                 <button className={`${styles.actionRowBtn} ${styles.deleteBtn}`} onClick={() => { if(confirm('Delete?')) deleteMutation.mutate(); }}>
                    <Trash2 size={16} /> Delete Task
                 </button>
              </div>

           </div>
        </div>
      </motion.div>
    </div>
  );
};

export default TaskDetailSlideOver;