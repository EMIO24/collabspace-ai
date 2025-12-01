import React from 'react';
import { Draggable } from 'react-beautiful-dnd';
import styles from './KanbanCard.module.css';

function KanbanCard({ task, index }) {
  const getPriorityColor = (priority) => {
    const colors = {
      high: '#ef4444',
      medium: '#f59e0b',
      low: '#10b981',
    };
    return colors[priority] || '#6b7280';
  };

  const formatDate = (date) => {
    if (!date) return null;
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <Draggable draggableId={task.id.toString()} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`${styles.card} ${snapshot.isDragging ? styles.dragging : ''}`}
        >
          <div className={styles.header}>
            <h4 className={styles.title}>{task.title}</h4>
            {task.priority && (
              <div
                className={styles.priorityDot}
                style={{ backgroundColor: getPriorityColor(task.priority) }}
                title={`${task.priority} priority`}
              />
            )}
          </div>

          {task.description && (
            <p className={styles.description}>{task.description}</p>
          )}

          <div className={styles.footer}>
            {task.dueDate && (
              <div className={styles.dueDate}>
                <svg className={styles.icon} viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                  <line x1="16" y1="2" x2="16" y2="6" />
                  <line x1="8" y1="2" x2="8" y2="6" />
                  <line x1="3" y1="10" x2="21" y2="10" />
                </svg>
                <span>{formatDate(task.dueDate)}</span>
              </div>
            )}

            {task.assignee && (
              <div className={styles.assignee}>
                <div className={styles.avatar} title={task.assignee.name}>
                  {task.assignee.avatar ? (
                    <img src={task.assignee.avatar} alt={task.assignee.name} />
                  ) : (
                    <span>{task.assignee.name.charAt(0).toUpperCase()}</span>
                  )}
                </div>
              </div>
            )}
          </div>

          {task.tags && task.tags.length > 0 && (
            <div className={styles.tags}>
              {task.tags.map((tag, idx) => (
                <span key={idx} className={styles.tag}>
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </Draggable>
  );
}

export default KanbanCard;