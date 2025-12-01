import React from 'react';
import StatusBadge from './StatusBadge';
import PriorityBadge from './PriorityBadge';
import DueDateDisplay from './DueDateDisplay';
import styles from './TaskListTable.module.css';

function TaskListTable({ 
  tasks, 
  selectedTasks = [], 
  onTaskClick, 
  onTaskDelete, 
  onSelectionChange 
}) {
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      onSelectionChange(tasks.map(t => t.id));
    } else {
      onSelectionChange([]);
    }
  };

  const handleSelectTask = (taskId) => {
    if (selectedTasks.includes(taskId)) {
      onSelectionChange(selectedTasks.filter(id => id !== taskId));
    } else {
      onSelectionChange([...selectedTasks, taskId]);
    }
  };

  if (tasks.length === 0) {
    return (
      <div className={styles.empty}>
        <svg className={styles.emptyIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M9 11l3 3L22 4" />
          <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
        </svg>
        <h3>No tasks found</h3>
        <p>Create a new task to get started</p>
      </div>
    );
  }

  return (
    <div className={styles.tableContainer}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th className={styles.checkboxCell}>
              <input
                type="checkbox"
                checked={selectedTasks.length === tasks.length && tasks.length > 0}
                onChange={handleSelectAll}
              />
            </th>
            <th className={styles.titleHeader}>Title</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Assignee</th>
            <th>Due Date</th>
            <th className={styles.actionsHeader}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr
              key={task.id}
              className={`${styles.row} ${selectedTasks.includes(task.id) ? styles.selected : ''}`}
            >
              <td className={styles.checkboxCell}>
                <input
                  type="checkbox"
                  checked={selectedTasks.includes(task.id)}
                  onChange={() => handleSelectTask(task.id)}
                  onClick={(e) => e.stopPropagation()}
                />
              </td>
              <td 
                className={styles.titleCell}
                onClick={() => onTaskClick(task.id)}
              >
                <div className={styles.taskTitle}>
                  {task.title}
                  {task.description && (
                    <span className={styles.description}>
                      {task.description.substring(0, 100)}
                      {task.description.length > 100 ? '...' : ''}
                    </span>
                  )}
                </div>
              </td>
              <td>
                <StatusBadge status={task.status} />
              </td>
              <td>
                <PriorityBadge priority={task.priority} />
              </td>
              <td>
                {task.assignee ? (
                  <div className={styles.assignee}>
                    <div className={styles.avatar}>
                      {task.assignee.avatar ? (
                        <img src={task.assignee.avatar} alt={task.assignee.name} />
                      ) : (
                        <span>{task.assignee.name.charAt(0).toUpperCase()}</span>
                      )}
                    </div>
                    <span className={styles.assigneeName}>{task.assignee.name}</span>
                  </div>
                ) : (
                  <span className={styles.unassigned}>Unassigned</span>
                )}
              </td>
              <td>
                <DueDateDisplay dueDate={task.dueDate} status={task.status} />
              </td>
              <td className={styles.actionsCell}>
                <button
                  className={styles.actionButton}
                  onClick={(e) => {
                    e.stopPropagation();
                    onTaskClick(task.id);
                  }}
                  title="View details"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                </button>
                <button
                  className={`${styles.actionButton} ${styles.deleteButton}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onTaskDelete(task.id);
                  }}
                  title="Delete"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                  </svg>
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default TaskListTable;