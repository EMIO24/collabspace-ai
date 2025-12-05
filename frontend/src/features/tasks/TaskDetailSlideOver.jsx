import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, Star, MoreHorizontal, Trash2, Send, Play, Square, 
  Copy, ArrowRight, Check
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
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
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState(TABS.COMMENTS);
  const [taskData, setTaskData] = useState(null);
  const [commentText, setCommentText] = useState('');
  
  // Move Project State
  const [isMoving, setIsMoving] = useState(false);

  // Time Tracking State
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const timerRef = useRef(null);

  const safeId = taskId ? String(taskId) : '';

  // 1. Fetch Task
  const { data: task } = useQuery({
    queryKey: ['task', taskId],
    queryFn: async () => {
      const res = await api.get(`/tasks/tasks/${taskId}/`);
      return res.data;
    },
    enabled: !!taskId
  });

  // 2. Fetch Comments
  const { data: rawComments } = useQuery({
    queryKey: ['taskComments', taskId],
    queryFn: async () => (await api.get(`/tasks/comments/?task=${taskId}`)).data,
    enabled: !!taskId && activeTab === TABS.COMMENTS
  });

  // 3. Fetch Time Entries
  const { data: rawTimeEntries } = useQuery({
    queryKey: ['taskTime', taskId],
    queryFn: async () => (await api.get(`/tasks/time-entries/?task=${taskId}`)).data,
    enabled: !!taskId && activeTab === TABS.TIME
  });

  // 4. Fetch Projects (For Move Functionality)
  const { data: projects } = useQuery({
    queryKey: ['allProjects'],
    queryFn: async () => {
      try {
        const res = await api.get('/projects/');
        return Array.isArray(res.data) ? res.data : (res.data.results || []);
      } catch { return []; }
    },
    enabled: isMoving // Only fetch when user clicks "Move"
  });

  const comments = useMemo(() => Array.isArray(rawComments) ? rawComments : (rawComments?.results || []), [rawComments]);
  const timeEntries = useMemo(() => Array.isArray(rawTimeEntries) ? rawTimeEntries : (rawTimeEntries?.results || []), [rawTimeEntries]);

  useEffect(() => {
    if (task) setTaskData(task);
  }, [task]);

  // --- MUTATIONS ---
  const updateMutation = useMutation({
    mutationFn: (updates) => api.patch(`/tasks/tasks/${taskId}/`, updates),
    onSuccess: () => {
      queryClient.invalidateQueries(['task', taskId]);
      queryClient.invalidateQueries(['tasks']);
      queryClient.invalidateQueries(['myTasks']); 
      toast.success('Saved');
    },
    onError: () => toast.error('Failed to update task')
  });

  const commentMutation = useMutation({
    mutationFn: (content) => api.post('/tasks/comments/', { task: taskId, content }),
    onSuccess: () => {
      queryClient.invalidateQueries(['taskComments', taskId]);
      setCommentText('');
      toast.success('Comment added');
    }
  });

  const duplicateMutation = useMutation({
    mutationFn: () => {
      // Strip ID and timestamps for the copy
      const { id, created_at, updated_at, ...rest } = taskData;
      return api.post('/tasks/tasks/', {
        ...rest,
        title: `Copy of ${rest.title}`,
        status: 'todo',
        project: rest.project
      });
    },
    onSuccess: () => {
      toast.success('Task duplicated');
      queryClient.invalidateQueries(['tasks']);
      onClose();
    },
    onError: () => toast.error('Failed to duplicate task')
  });

  const moveProjectMutation = useMutation({
    mutationFn: (projectId) => api.patch(`/tasks/tasks/${taskId}/`, { project: projectId }),
    onSuccess: () => {
      toast.success('Task moved to new project');
      queryClient.invalidateQueries(['tasks']);
      setIsMoving(false);
      onClose();
    },
    onError: () => toast.error('Failed to move task')
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`/tasks/tasks/${taskId}/`),
    onSuccess: () => {
      toast.success('Task deleted');
      onClose();
      queryClient.invalidateQueries(['tasks']);
    }
  });

  const timeEntryMutation = useMutation({
    mutationFn: (minutes) => api.post('/tasks/time-entries/', { 
      task: taskId, 
      duration: minutes, 
      description: 'Timer Log' 
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['taskTime', taskId]);
      toast.success('Time logged');
    }
  });

  // --- HANDLERS ---
  const handleFieldChange = (field, value) => {
    setTaskData(prev => ({ ...prev, [field]: value }));
  };

  const handleBlur = (field) => {
    if (taskData[field] !== task[field]) {
      updateMutation.mutate({ [field]: taskData[field] });
    }
  };

  // --- TIMER LOGIC ---
  const toggleTimer = () => {
    if (isTimerRunning) {
      clearInterval(timerRef.current);
      setIsTimerRunning(false);
      if (timerSeconds > 60) {
        timeEntryMutation.mutate(Math.ceil(timerSeconds / 60));
      }
      setTimerSeconds(0);
    } else {
      setIsTimerRunning(true);
      timerRef.current = setInterval(() => {
        setTimerSeconds(prev => prev + 1);
      }, 1000);
    }
  };

  const formatTimer = (totalSeconds) => {
    const h = Math.floor(totalSeconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((totalSeconds % 3600) / 60).toString().padStart(2, '0');
    const s = (totalSeconds % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  };

  if (!taskId || !taskData) return null;

  return (
    <AnimatePresence>
      <div className={styles.backdrop} onClick={onClose}>
        <motion.div 
          className={styles.panel}
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: "spring", damping: 25, stiffness: 200 }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className={styles.header}>
            <div style={{display:'flex', alignItems:'center', gap:'1rem'}}>
               <span className={styles.taskId}>TASK-{safeId.slice(0, 8)}</span>
               <button className={styles.iconBtn} onClick={() => updateMutation.mutate({ is_favorite: !taskData.is_favorite })}>
                  <Star size={18} className={taskData.is_favorite ? styles.starActive : ''} fill={taskData.is_favorite ? "currentColor" : "none"} />
               </button>
            </div>
            <div className={styles.headerActions}>
               <button className={styles.iconBtn}><MoreHorizontal size={18} /></button>
               <button className={styles.iconBtn} onClick={onClose}><X size={20} /></button>
            </div>
          </div>

          <div className={styles.body}>
            {/* Main Content (Left) */}
            <div className={styles.mainContent}>
               <input 
                  className={styles.titleInput}
                  value={taskData.title || ''}
                  onChange={(e) => handleFieldChange('title', e.target.value)}
                  onBlur={() => handleBlur('title')}
                  placeholder="Task Title"
               />
               
               <textarea
                  className={styles.descriptionArea}
                  value={taskData.description || ''}
                  onChange={(e) => handleFieldChange('description', e.target.value)}
                  onBlur={() => handleBlur('description')}
                  placeholder="Add a detailed description..."
               />

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

               {activeTab === TABS.COMMENTS && (
                 <div className={styles.commentSection}>
                   <div className={styles.commentInputWrapper}>
                      <textarea 
                        className={styles.commentInput} 
                        placeholder="Write a comment..." 
                        value={commentText}
                        onChange={(e) => setCommentText(e.target.value)}
                      />
                      <div className={styles.commentToolbar}>
                         <Button size="sm" onClick={() => commentMutation.mutate(commentText)} disabled={!commentText}>
                            <Send size={14} className="mr-2" /> Comment
                         </Button>
                      </div>
                   </div>
                   
                   <div className={styles.commentList}>
                      {comments.map((comment, i) => (
                        <div key={comment.id || i} className={styles.comment}>
                           <Avatar src={comment.user?.avatar} fallback={comment.user?.username?.[0] || 'U'} />
                           <div className={styles.commentContent}>
                              <div className={styles.commentHeader}>
                                 <span className={styles.commentAuthor}>{comment.user?.username}</span>
                                 <span className={styles.commentTime}>
                                    {new Date(comment.created_at).toLocaleString()}
                                 </span>
                              </div>
                              <div className={styles.commentText}>{comment.content}</div>
                           </div>
                        </div>
                      ))}
                   </div>
                 </div>
               )}

               {activeTab === TABS.TIME && (
                  <div>
                     <div className={styles.timerWidget}>
                        <div>
                           <div className="text-xs font-bold text-blue-600 uppercase mb-1">Current Session</div>
                           <div className={styles.timerDisplay}>{formatTimer(timerSeconds)}</div>
                        </div>
                        <div className={styles.timerControls}>
                           {!isTimerRunning ? (
                              <Button onClick={toggleTimer} className="bg-green-600 hover:bg-green-700">
                                 <Play size={16} className="mr-2" /> Start Timer
                              </Button>
                           ) : (
                              <Button onClick={toggleTimer} className="bg-red-500 hover:bg-red-600">
                                 <Square size={16} className="mr-2" /> Stop
                              </Button>
                           )}
                        </div>
                     </div>
                     <h4 className="font-bold text-gray-700 mb-4">Time Log</h4>
                     <div className={styles.timeLogList}>
                        {timeEntries.map((entry, i) => (
                           <div key={i} className={styles.timeEntry}>
                              <span className="text-sm font-semibold text-gray-800">Logged Time</span>
                              <div className="font-mono font-bold text-gray-700">{entry.duration || entry.hours}h</div>
                           </div>
                        ))}
                        {!timeEntries.length && <div className="text-gray-400 italic">No time logged yet.</div>}
                     </div>
                  </div>
               )}
               
               {activeTab === TABS.ATTACHMENTS && <div className="text-gray-400 text-center p-8">Attachments functionality is handled in Project Files.</div>}
               {activeTab === TABS.ACTIVITY && <div className="text-gray-400 text-center p-8">Activity log loading...</div>}
            </div>

            {/* Sidebar (Right) */}
            <div className={styles.sidebar}>
               <div className={styles.sidebarSection}>
                  <label className={styles.propertyLabel}>Status</label>
                  <select 
                     className={styles.select}
                     value={taskData.status || 'todo'}
                     onChange={(e) => {
                       handleFieldChange('status', e.target.value);
                       updateMutation.mutate({ status: e.target.value });
                     }}
                  >
                     <option value="todo">To Do</option>
                     <option value="in_progress">In Progress</option>
                     <option value="review">Review</option>
                     <option value="done">Done</option>
                  </select>
               </div>

               <div className={styles.sidebarSection}>
                  <label className={styles.propertyLabel}>Priority</label>
                  <select 
                     className={styles.select}
                     value={taskData.priority || 'medium'}
                     onChange={(e) => {
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
                  <label className={styles.propertyLabel}>Due Date</label>
                  <input 
                     type="date" 
                     className={styles.dateInput}
                     value={taskData.due_date ? taskData.due_date.split('T')[0] : ''} 
                     onChange={(e) => {
                        handleFieldChange('due_date', e.target.value);
                        updateMutation.mutate({ due_date: e.target.value });
                     }}
                  />
               </div>

               <div className={styles.sidebarFooter}>
                  <button 
                    className={styles.actionRowBtn} 
                    onClick={() => duplicateMutation.mutate()}
                    disabled={duplicateMutation.isPending}
                  >
                     <Copy size={16} /> {duplicateMutation.isPending ? 'Duplicating...' : 'Duplicate Task'}
                  </button>
                  
                  {!isMoving ? (
                    <button className={styles.actionRowBtn} onClick={() => setIsMoving(true)}>
                       <ArrowRight size={16} /> Move to Project
                    </button>
                  ) : (
                    <div className="bg-white p-2 rounded border border-blue-200 shadow-sm">
                       <p className="text-xs text-gray-500 mb-1 font-semibold">Select Project:</p>
                       <select 
                         className={styles.select} 
                         onChange={(e) => { if(e.target.value) moveProjectMutation.mutate(e.target.value) }}
                         defaultValue=""
                       >
                          <option value="" disabled>Choose...</option>
                          {projects?.map(p => (
                            <option key={p.id} value={p.id}>{p.name}</option>
                          ))}
                       </select>
                       <button className="text-xs text-red-500 mt-1 hover:underline w-full text-left" onClick={() => setIsMoving(false)}>Cancel</button>
                    </div>
                  )}

                  <button 
                    className={`${styles.actionRowBtn} ${styles.deleteBtn}`} 
                    onClick={() => { if(confirm('Delete this task?')) deleteMutation.mutate(); }}
                  >
                     <Trash2 size={16} /> Delete Task
                  </button>
               </div>

            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default TaskDetailSlideOver;