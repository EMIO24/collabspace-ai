import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Calendar, CheckSquare, MessageSquare, Paperclip } from 'lucide-react';
import Avatar from '../../components/ui/Avatar/Avatar';
import styles from './TaskCard.module.css';

const TaskCard = ({ task, onClick }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id: task.id, data: { ...task } });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const priorityColors = {
    low: '#3b82f6',      // Blue
    medium: '#f59e0b',   // Orange
    high: '#ef4444',     // Red
    urgent: '#7c3aed'    // Purple
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`${styles.card} ${isDragging ? styles.isDragging : ''}`}
      onClick={onClick}
    >
      <div className={styles.header}>
        <div 
          className={styles.priorityDot} 
          style={{ background: priorityColors[task.priority] || '#ccc' }} 
          title={`Priority: ${task.priority}`}
        />
        <div className={styles.checkbox}>
          {task.status === 'done' ? <CheckSquare size={16} className="text-green-500" /> : <div className={styles.emptyCheck} />}
        </div>
      </div>
      
      <h4 className={styles.title}>{task.title}</h4>
      
      {/* Labels / Tags */}
      {task.tags && task.tags.length > 0 && (
        <div className={styles.tags}>
           {task.tags.map((tag, i) => (
             <span key={i} className={styles.tag} style={{ background: tag.color || '#e0f2fe', color: tag.text_color || '#0369a1' }}>
               {tag.name}
             </span>
           ))}
        </div>
      )}

      <div className={styles.footer}>
        <div className={styles.metaLeft}>
           {task.due_date && (
             <span className={`${styles.metaItem} ${new Date(task.due_date) < new Date() ? styles.overdue : ''}`}>
               <Calendar size={12} /> 
               {new Date(task.due_date).toLocaleDateString(undefined, {month:'short', day:'numeric'})}
             </span>
           )}
           
           {/* Activity Counts */}
           {(task.comment_count > 0 || task.attachment_count > 0) && (
             <div className={styles.counts}>
               {task.comment_count > 0 && (
                 <span className={styles.metaItem}>
                   <MessageSquare size={12} /> {task.comment_count}
                 </span>
               )}
               {task.attachment_count > 0 && (
                 <span className={styles.metaItem}>
                   <Paperclip size={12} /> {task.attachment_count}
                 </span>
               )}
             </div>
           )}
        </div>

        {task.assigned_to && (
          <Avatar 
            src={task.assigned_to.avatar} 
            fallback={task.assigned_to.username?.[0] || 'U'} 
            size="xs" 
          />
        )}
      </div>
    </div>
  );
};

export default TaskCard;