import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTask, updateTask, deleteTask } from '../../api/tasks';
import StatusBadge from '../../components/task/StatusBadge';
import PriorityBadge from '../../components/task/PriorityBadge';
import DueDateDisplay from '../../components/task/DueDateDisplay';
import TaskComments from '../../components/task/TaskComments';
import TaskAttachments from '../../components/task/TaskAttachments';
import SubtasksList from '../../components/task/SubtasksList';
import TimeTracking from '../../components/task/TimeTracking';
import RichTextEditor from '../../components/task/RichTextEditor';
import styles from './TaskDetailPage.module.css';

function TaskDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({});

  useEffect(() => {
    loadTask();
  }, [id]);

  const loadTask = async () => {
    try {
      setLoading(true);
      const response = await getTask(id);
      setTask(response.data);
      setEditForm(response.data);
    } catch (error) {
      console.error('Failed to load task:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (updates) => {
    try {
      const response = await updateTask(id, updates);
      setTask(response.data);
      setEditForm(response.data);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await deleteTask(id);
        navigate('/tasks');
      } catch (error) {
        console.error('Failed to delete task:', error);
      }
    }
  };

  const handleQuickUpdate = async (field, value) => {
    const updates = { [field]: value };
    await handleUpdate(updates);
  };

  if (loading) {
    return <div className={styles.loading}>Loading task...</div>;
  }

  if (!task) {
    return <div className={styles.error}>Task not found</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <button className={styles.backButton} onClick={() => navigate('/tasks')}>
          ← Back to Tasks
        </button>
        <div className={styles.actions}>
          <button 
            className={styles.editButton}
            onClick={() => setIsEditing(!isEditing)}
          >
            {isEditing ? 'Cancel' : 'Edit'}
          </button>
          <button className={styles.deleteButton} onClick={handleDelete}>
            Delete
          </button>
        </div>
      </div>

      <div className={styles.content}>
        <div className={styles.mainSection}>
          <div className={styles.titleSection}>
            {isEditing ? (
              <input
                type="text"
                className={styles.titleInput}
                value={editForm.title}
                onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
              />
            ) : (
              <h1 className={styles.title}>{task.title}</h1>
            )}
            <div className={styles.badges}>
              <StatusBadge 
                status={task.status}
                editable={!isEditing}
                onChange={(status) => handleQuickUpdate('status', status)}
              />
              <PriorityBadge
                priority={task.priority}
                editable={!isEditing}
                onChange={(priority) => handleQuickUpdate('priority', priority)}
              />
            </div>
          </div>

          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Description</h2>
            {isEditing ? (
              <RichTextEditor
                value={editForm.description || ''}
                onChange={(value) => setEditForm({ ...editForm, description: value })}
                placeholder="Enter task description..."
              />
            ) : (
              <div className={styles.description}>
                {task.description || 'No description provided'}
              </div>
            )}
          </div>

          {isEditing && (
            <div className={styles.saveActions}>
              <button
                className={styles.cancelButton}
                onClick={() => {
                  setIsEditing(false);
                  setEditForm(task);
                }}
              >
                Cancel
              </button>
              <button
                className={styles.saveButton}
                onClick={() => handleUpdate(editForm)}
              >
                Save Changes
              </button>
            </div>
          )}

          <SubtasksList taskId={id} />

          <TaskComments taskId={id} />
        </div>

        <div className={styles.sidebar}>
          <div className={styles.sidebarSection}>
            <h3 className={styles.sidebarTitle}>Details</h3>
            <div className={styles.detailsList}>
              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Assignee</span>
                <div className={styles.detailValue}>
                  {task.assignee ? (
                    <div className={styles.assignee}>
                      <div className={styles.avatar}>
                        {task.assignee.avatar ? (
                          <img src={task.assignee.avatar} alt={task.assignee.name} />
                        ) : (
                          <span>{task.assignee.name.charAt(0).toUpperCase()}</span>
                        )}
                      </div>
                      <span>{task.assignee.name}</span>
                    </div>
                  ) : (
                    <span className={styles.notSet}>Unassigned</span>
                  )}
                </div>
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Due Date</span>
                <DueDateDisplay
                  dueDate={task.dueDate}
                  status={task.status}
                />
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Created</span>
                <span className={styles.detailValue}>
                  {new Date(task.createdAt).toLocaleDateString()}
                </span>
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Updated</span>
                <span className={styles.detailValue}>
                  {new Date(task.updatedAt).toLocaleDateString()}
                </span>
              </div>

              {task.project && (
                <div className={styles.detailItem}>
                  <span className={styles.detailLabel}>Project</span>
                  <span className={styles.detailValue}>{task.project.name}</span>
                </div>
              )}
            </div>
          </div>

          <TimeTracking taskId={id} />

          <TaskAttachments taskId={id} />
        </div>
      </div>
    </div>
  );
}

export default TaskDetailPage;