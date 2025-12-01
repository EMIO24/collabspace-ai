import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import Avatar from '../../components/ui/Avatar/Avatar';
import styles from './TaskCard.module.css';

const TaskCard = ({ task }) => {
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

  const priorityClass = styles[`priority_${task.priority}`] || styles.priority_low;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`${styles.card} ${isDragging ? styles.isDragging : ''}`}
    >
      <h4 className={styles.title}>{task.title}</h4>
      <div className={styles.footer}>
        <span className={`${styles.priority} ${priorityClass}`}>
          {task.priority}
        </span>
        {task.assigned_to && (
          <Avatar 
            src={task.assigned_to.avatar} 
            fallback={task.assigned_to.username[0]} 
            size="sm" 
          />
        )}
      </div>
    </div>
  );
};

export default TaskCard;