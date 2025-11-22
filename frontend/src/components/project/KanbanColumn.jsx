import React from 'react';
import { Droppable } from 'react-beautiful-dnd';
import KanbanCard from './KanbanCard';
import styles from './KanbanColumn.module.css';

function KanbanColumn({ column }) {
  const getColumnColor = (id) => {
    const colors = {
      todo: '#3b82f6',
      inProgress: '#f59e0b',
      review: '#8b5cf6',
      done: '#10b981',
    };
    return colors[id] || '#6b7280';
  };

  return (
    <div className={styles.column}>
      <div className={styles.header}>
        <div className={styles.titleContainer}>
          <div
            className={styles.indicator}
            style={{ backgroundColor: getColumnColor(column.id) }}
          />
          <h3 className={styles.title}>{column.title}</h3>
          <span className={styles.count}>{column.tasks.length}</span>
        </div>
      </div>

      <Droppable droppableId={column.id}>
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className={`${styles.taskList} ${snapshot.isDraggingOver ? styles.draggingOver : ''}`}
          >
            {column.tasks.map((task, index) => (
              <KanbanCard key={task.id} task={task} index={index} />
            ))}
            {provided.placeholder}
            {column.tasks.length === 0 && (
              <div className={styles.empty}>No tasks</div>
            )}
          </div>
        )}
      </Droppable>
    </div>
  );
}

export default KanbanColumn;