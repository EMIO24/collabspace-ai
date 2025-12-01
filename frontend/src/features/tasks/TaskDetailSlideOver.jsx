import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { X, MessageSquare, Paperclip, Clock, Send, Upload, File } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Avatar from '../../components/ui/Avatar/Avatar';
import Button from '../../components/ui/Button/Button';
import styles from './TaskDetailSlideOver.module.css';

const TaskDetailSlideOver = ({ taskId, onClose }) => {
  const queryClient = useQueryClient();
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  // --- FETCH TASK DETAILS ---
  const { data: task, isLoading: isTaskLoading } = useQuery({
    queryKey: ['task', taskId],
    queryFn: async () => {
      const res = await api.get(`/tasks/tasks/${taskId}/`);
      return res.data;
    },
    enabled: !!taskId
  });

  // --- FETCH COMMENTS ---
  const { data: comments } = useQuery({
    queryKey: ['comments', taskId],
    queryFn: async () => {
      const res = await api.get(`/tasks/comments/?task=${taskId}`);
      return res.data;
    },
    enabled: !!taskId
  });

  // --- MUTATIONS ---
  
  // 1. Update Task (Title/Desc) on Blur
  const updateTaskMutation = useMutation({
    mutationFn: (updates) => api.put(`/tasks/tasks/${taskId}/`, updates),
    onSuccess: () => {
      queryClient.invalidateQueries(['task', taskId]);
      queryClient.invalidateQueries(['tasks']); // Update board
      toast.success('Saved');
    }
  });

  const handleBlur = (field, value) => {
    if (task && task[field] !== value) {
      updateTaskMutation.mutate({ [field]: value });
    }
  };

  // 2. Post Comment
  const [commentText, setCommentText] = useState('');
  const commentMutation = useMutation({
    mutationFn: (text) => api.post('/tasks/comments/', { task: taskId, content: text }),
    onSuccess: () => {
      queryClient.invalidateQueries(['comments', taskId]);
      setCommentText('');
    }
  });

  // 3. Upload Attachment
  const attachmentMutation = useMutation({
    mutationFn: (formData) => {
      // Assuming multipart/form-data request
      return api.post('/tasks/attachments/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
    },
    onSuccess: () => {
      toast.success('File uploaded');
      // Refetch task or attachments depending on API structure
      queryClient.invalidateQueries(['task', taskId]); 
    }
  });

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) handleUpload(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const handleUpload = (file) => {
    const formData = new FormData();
    formData.append('task', taskId);
    formData.append('file', file);
    attachmentMutation.mutate(formData);
  };

  // 4. Log Time
  const [timeSpent, setTimeSpent] = useState('');
  const timeLogMutation = useMutation({
    mutationFn: (minutes) => api.post('/tasks/time-entries/', { task: taskId, duration: minutes }),
    onSuccess: () => {
      toast.success('Time logged');
      setTimeSpent('');
    }
  });

  if (!taskId) return null;

  return (
    <AnimatePresence>
      <motion.div 
        className={styles.backdrop}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
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
            <span className="text-sm font-semibold text-gray-500">TASK-{taskId.slice(0, 8)}</span>
            <button className={styles.closeBtn} onClick={onClose}>
              <X size={20} />
            </button>
          </div>

          {/* Content */}
          {isTaskLoading ? (
             <div className="flex items-center justify-center h-full">Loading...</div>
          ) : (
            <div className={styles.scrollArea}>
              
              {/* Editable Details */}
              <div>
                <input
                  className={styles.titleInput}
                  defaultValue={task.title}
                  onBlur={(e) => handleBlur('title', e.target.value)}
                  placeholder="Task Title"
                />
                <textarea
                  className={styles.descInput}
                  defaultValue={task.description}
                  onBlur={(e) => handleBlur('description', e.target.value)}
                  placeholder="Add a description..."
                />
              </div>

              {/* Time Tracking */}
              <div>
                <h4 className={styles.sectionTitle}>
                  <Clock size={16} /> Time Tracking
                </h4>
                <div className={styles.timeLogForm}>
                  <input 
                    type="number" 
                    placeholder="Mins" 
                    className={styles.timeInput}
                    value={timeSpent}
                    onChange={(e) => setTimeSpent(e.target.value)}
                  />
                  <Button 
                    size="sm" 
                    variant="ghost" 
                    onClick={() => timeLogMutation.mutate(timeSpent)}
                    disabled={!timeSpent}
                  >
                    Log Time
                  </Button>
                </div>
              </div>

              {/* Attachments */}
              <div>
                <h4 className={styles.sectionTitle}>
                  <Paperclip size={16} /> Attachments
                </h4>
                <div 
                  className={`${styles.dropZone} ${isDragging ? styles.dropZoneActive : ''}`}
                  onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload size={24} className="mx-auto mb-2 opacity-50" />
                  <p>Click or drag file to upload</p>
                  <input 
                    type="file" 
                    hidden 
                    ref={fileInputRef} 
                    onChange={handleFileSelect} 
                  />
                </div>
                {/* Simple list of existing attachments (mocked based on logic) */}
                {task.attachments && task.attachments.length > 0 && (
                  <div className={styles.fileList}>
                    {task.attachments.map((file) => (
                      <div key={file.id} className={styles.fileItem}>
                        <File size={16} className="text-blue-500" />
                        <span className="flex-1 truncate">{file.name}</span>
                        <a href={file.url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 hover:underline">Download</a>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Comments */}
              <div>
                <h4 className={styles.sectionTitle}>
                  <MessageSquare size={16} /> Comments
                </h4>
                
                <div className={styles.commentList}>
                  {comments?.map((comment) => (
                    <div key={comment.id} className={styles.comment}>
                      <Avatar 
                        src={comment.user.avatar} 
                        fallback={comment.user.username[0]} 
                        size="sm" 
                      />
                      <div>
                        <div className={styles.commentMeta}>
                          {comment.user.username} • {new Date(comment.created_at).toLocaleString()}
                        </div>
                        <div className={styles.commentBody}>
                          {comment.content}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className={styles.commentForm}>
                  <input
                    className={styles.commentInput}
                    placeholder="Write a comment..."
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && commentMutation.mutate(commentText)}
                  />
                  <Button 
                    size="sm" 
                    onClick={() => commentMutation.mutate(commentText)}
                    disabled={!commentText}
                  >
                    <Send size={16} />
                  </Button>
                </div>
              </div>

            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default TaskDetailSlideOver;