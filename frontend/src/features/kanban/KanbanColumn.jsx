import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { Plus } from 'lucide-react';
import TaskCard from './TaskCard';
import styles from './KanbanColumn.module.css';

const KanbanColumn = ({ id, title, tasks, onTaskClick, onAddTask }) => {
  const { setNodeRef } = useDroppable({ id });

  return (
    <div className={styles.column}>
      <div className={styles.header}>
        <h3 className={styles.title}>
          {title}
          <span className={styles.count}>{tasks.length}</span>
        </h3>
      </div>

      {/* Inline Add Button */}
      <button className={styles.addBtn} onClick={() => onAddTask(id)}>
        <Plus size={14} /> Add Task
      </button>
      
      <div ref={setNodeRef} className={styles.taskList}>
        <SortableContext 
          id={id} 
          items={tasks.map(t => t.id)} 
          strategy={verticalListSortingStrategy}
        >
          {tasks.map((task) => (
            <TaskCard 
                key={task.id} 
                task={task} 
                onClick={() => onTaskClick(task.id)} 
            />
          ))}
        </SortableContext>
      </div>
    </div>
  );
};

export default KanbanColumn;