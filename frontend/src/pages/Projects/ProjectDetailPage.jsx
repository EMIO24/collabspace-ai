import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProject, updateProject, deleteProject } from '../../api/projects';
import { getTasks, createTask } from '../../api/tasks';
import styles from './ProjectDetailPage.module.css';

function ProjectDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    loadProjectData();
  }, [id]);

  const loadProjectData = async () => {
    try {
      setLoading(true);
      const [projectRes, tasksRes] = await Promise.all([
        getProject(id),
        getTasks({ projectId: id })
      ]);
      setProject(projectRes.data);
      setTasks(tasksRes.data);
    } catch (error) {
      console.error('Failed to load project:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProject = async (updates) => {
    try {
      const response = await updateProject(id, updates);
      setProject(response.data);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update project:', error);
    }
  };

  const handleDeleteProject = async () => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      try {
        await deleteProject(id);
        navigate('/projects');
      } catch (error) {
        console.error('Failed to delete project:', error);
      }
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      planning: '#3b82f6',
      active: '#10b981',
      on_hold: '#f59e0b',
      completed: '#6b7280'
    };
    return colors[status] || '#6b7280';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      high: '#ef4444',
      medium: '#f59e0b',
      low: '#10b981'
    };
    return colors[priority] || '#6b7280';
  };

  const taskStats = {
    total: tasks.length,
    completed: tasks.filter(t => t.status === 'done').length,
    inProgress: tasks.filter(t => t.status === 'in_progress').length,
    todo: tasks.filter(t => t.status === 'todo').length
  };

  const completionPercentage = taskStats.total > 0
    ? Math.round((taskStats.completed / taskStats.total) * 100)
    : 0;

  if (loading) {
    return <div className={styles.loading}>Loading project...</div>;
  }

  if (!project) {
    return <div className={styles.error}>Project not found</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <button className={styles.backButton} onClick={() => navigate('/projects')}>
          ← Back to Projects
        </button>
        <div className={styles.actions}>
          <button className={styles.editButton} onClick={() => setIsEditing(!isEditing)}>
            {isEditing ? 'Cancel' : 'Edit'}
          </button>
          <button className={styles.deleteButton} onClick={handleDeleteProject}>
            Delete
          </button>
        </div>
      </div>

      <div className={styles.titleSection}>
        <h1 className={styles.title}>{project.name}</h1>
        <div className={styles.badges}>
          <span 
            className={styles.badge}
            style={{ backgroundColor: getStatusColor(project.status) }}
          >
            {project.status?.replace('_', ' ')}
          </span>
          <span 
            className={styles.badge}
            style={{ backgroundColor: getPriorityColor(project.priority) }}
          >
            {project.priority} priority
          </span>
        </div>
      </div>

      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'overview' ? styles.active : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'tasks' ? styles.active : ''}`}
          onClick={() => setActiveTab('tasks')}
        >
          Tasks ({taskStats.total})
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'team' ? styles.active : ''}`}
          onClick={() => setActiveTab('team')}
        >
          Team
        </button>
      </div>

      <div className={styles.content}>
        {activeTab === 'overview' && (
          <div className={styles.overview}>
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>Description</h2>
              <p className={styles.description}>{project.description || 'No description provided'}</p>
            </div>

            <div className={styles.statsGrid}>
              <div className={styles.statCard}>
                <div className={styles.statLabel}>Progress</div>
                <div className={styles.statValue}>{completionPercentage}%</div>
                <div className={styles.progressBar}>
                  <div 
                    className={styles.progressFill}
                    style={{ width: `${completionPercentage}%` }}
                  />
                </div>
              </div>

              <div className={styles.statCard}>
                <div className={styles.statLabel}>Total Tasks</div>
                <div className={styles.statValue}>{taskStats.total}</div>
              </div>

              <div className={styles.statCard}>
                <div className={styles.statLabel}>Completed</div>
                <div className={styles.statValue}>{taskStats.completed}</div>
              </div>

              <div className={styles.statCard}>
                <div className={styles.statLabel}>In Progress</div>
                <div className={styles.statValue}>{taskStats.inProgress}</div>
              </div>
            </div>

            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>Details</h2>
              <div className={styles.detailsGrid}>
                <div className={styles.detail}>
                  <span className={styles.detailLabel}>Start Date:</span>
                  <span className={styles.detailValue}>
                    {project.startDate ? new Date(project.startDate).toLocaleDateString() : 'Not set'}
                  </span>
                </div>
                <div className={styles.detail}>
                  <span className={styles.detailLabel}>End Date:</span>
                  <span className={styles.detailValue}>
                    {project.endDate ? new Date(project.endDate).toLocaleDateString() : 'Not set'}
                  </span>
                </div>
                <div className={styles.detail}>
                  <span className={styles.detailLabel}>Created:</span>
                  <span className={styles.detailValue}>
                    {new Date(project.createdAt).toLocaleDateString()}
                  </span>
                </div>
                <div className={styles.detail}>
                  <span className={styles.detailLabel}>Budget:</span>
                  <span className={styles.detailValue}>
                    {project.budget ? `$${project.budget.toLocaleString()}` : 'Not set'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'tasks' && (
          <div className={styles.tasks}>
            <div className={styles.taskList}>
              {tasks.length === 0 ? (
                <div className={styles.empty}>No tasks yet</div>
              ) : (
                tasks.map(task => (
                  <div key={task.id} className={styles.taskItem}>
                    <input type="checkbox" checked={task.status === 'done'} readOnly />
                    <div className={styles.taskContent}>
                      <div className={styles.taskTitle}>{task.title}</div>
                      <div className={styles.taskMeta}>
                        {task.assignee && <span>Assigned to {task.assignee.name}</span>}
                        {task.dueDate && <span>Due {new Date(task.dueDate).toLocaleDateString()}</span>}
                      </div>
                    </div>
                    <span className={styles.taskStatus}>{task.status}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'team' && (
          <div className={styles.team}>
            <div className={styles.empty}>Team management coming soon</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProjectDetailPage;