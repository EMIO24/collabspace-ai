import React, { useState, useEffect } from 'react';
import { getSubtasks, createSubtask, updateSubtask, deleteSubtask } from '../../api/subtasks';
import styles from './SubtasksList.module.css';

function SubtasksList({ taskId }) {
  const [subtasks, setSubtasks] = useState([]);
  const [newSubtaskTitle, setNewSubtaskTitle] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  useEffect(() => {
    loadSubtasks();
  }, [taskId]);

  const loadSubtasks = async () => {
    try {
      const response = await getSubtasks(taskId);
      setSubtasks(response.data);
    } catch (error) {
      console.error('Failed to load subtasks:', error);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newSubtaskTitle.trim()) return;

    try {
      const response = await createSubtask({
        taskId,
        title: newSubtaskTitle,
        completed: false,
      });
      setSubtasks([...subtasks, response.data]);
      setNewSubtaskTitle('');
      setIsAdding(false);
    } catch (error) {
      console.error('Failed to create subtask:', error);
    }
  };

  const handleToggle = async (subtaskId, completed) => {
    try {
      const response = await updateSubtask(subtaskId, { completed: !completed });
      setSubtasks(subtasks.map(st => 
        st.id === subtaskId ? response.data : st
      ));
    } catch (error) {
      console.error('Failed to update subtask:', error);
    }
  };

  const handleDelete = async (subtaskId) => {
    try {
      await deleteSubtask(subtaskId);
      setSubtasks(subtasks.filter(st => st.id !== subtaskId));
    } catch (error) {
      console.error('Failed to delete subtask:', error);
    }
  };

  const completedCount = subtasks.filter(st => st.completed).length;
  const progressPercentage = subtasks.length > 0 
    ? Math.round((completedCount / subtasks.length) * 100)
    : 0;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>
          Subtasks ({completedCount}/{subtasks.length})
        </h2>
        {subtasks.length > 0 && (
          <div className={styles.progress}>
            <div className={styles.progressBar}>
              <div 
                className={styles.progressFill}
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
            <span className={styles.progressText}>{progressPercentage}%</span>
          </div>
        )}
      </div>

      <div className={styles.subtasksList}>
        {subtasks.map(subtask => (
          <div key={subtask.id} className={styles.subtask}>
            <input
              type="checkbox"
              className={styles.checkbox}
              checked={subtask.completed}
              onChange={() => handleToggle(subtask.id, subtask.completed)}
            />
            <span className={`${styles.subtaskTitle} ${subtask.completed ? styles.completed : ''}`}>
              {subtask.title}
            </span>
            <button
              className={styles.deleteButton}
              onClick={() => handleDelete(subtask.id)}
              title="Delete subtask"
            >
              ×
            </button>
          </div>
        ))}
      </div>

      {isAdding ? (
        <form onSubmit={handleAdd} className={styles.addForm}>
          <input
            type="text"
            className={styles.input}
            value={newSubtaskTitle}
            onChange={(e) => setNewSubtaskTitle(e.target.value)}
            placeholder="Enter subtask title"
            autoFocus
          />
          <div className={styles.formActions}>
            <button type="submit" className={styles.saveButton}>
              Add
            </button>
            <button
              type="button"
              className={styles.cancelButton}
              onClick={() => {
                setIsAdding(false);
                setNewSubtaskTitle('');
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <button
          className={styles.addButton}
          onClick={() => setIsAdding(true)}
        >
          + Add Subtask
        </button>
      )}
    </div>
  );
}

export default SubtasksList;