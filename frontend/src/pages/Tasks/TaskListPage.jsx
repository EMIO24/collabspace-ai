import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTasks, deleteTask } from '../../api/tasks';
import TaskFilters from '../../components/task/TaskFilters';
import TaskListTable from '../../components/task/TaskListTable';
import CreateTaskModal from '../../components/task/CreateTaskModal';
import styles from './TaskListPage.module.css';

function TaskListPage() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [filteredTasks, setFilteredTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState('table'); // table or grid
  const [selectedTasks, setSelectedTasks] = useState([]);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const response = await getTasks();
      setTasks(response.data);
      setFilteredTasks(response.data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (filters) => {
    let filtered = [...tasks];

    if (filters.search) {
      filtered = filtered.filter(task =>
        task.title.toLowerCase().includes(filters.search.toLowerCase()) ||
        task.description?.toLowerCase().includes(filters.search.toLowerCase())
      );
    }

    if (filters.status && filters.status !== 'all') {
      filtered = filtered.filter(task => task.status === filters.status);
    }

    if (filters.priority && filters.priority !== 'all') {
      filtered = filtered.filter(task => task.priority === filters.priority);
    }

    if (filters.assignee && filters.assignee !== 'all') {
      filtered = filtered.filter(task => task.assigneeId === filters.assignee);
    }

    if (filters.sortBy) {
      filtered.sort((a, b) => {
        switch (filters.sortBy) {
          case 'title':
            return a.title.localeCompare(b.title);
          case 'dueDate':
            return new Date(a.dueDate || 0) - new Date(b.dueDate || 0);
          case 'priority':
            const priorityOrder = { high: 3, medium: 2, low: 1 };
            return (priorityOrder[b.priority] || 0) - (priorityOrder[a.priority] || 0);
          case 'created':
            return new Date(b.createdAt) - new Date(a.createdAt);
          default:
            return 0;
        }
      });
    }

    setFilteredTasks(filtered);
  };

  const handleTaskCreated = (newTask) => {
    setTasks([newTask, ...tasks]);
    setFilteredTasks([newTask, ...filteredTasks]);
    setIsCreateModalOpen(false);
  };

  const handleTaskClick = (taskId) => {
    navigate(`/tasks/${taskId}`);
  };

  const handleTaskDelete = async (taskId) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await deleteTask(taskId);
        setTasks(tasks.filter(t => t.id !== taskId));
        setFilteredTasks(filteredTasks.filter(t => t.id !== taskId));
      } catch (error) {
        console.error('Failed to delete task:', error);
      }
    }
  };

  const handleBulkDelete = async () => {
    if (window.confirm(`Delete ${selectedTasks.length} selected tasks?`)) {
      try {
        await Promise.all(selectedTasks.map(id => deleteTask(id)));
        setTasks(tasks.filter(t => !selectedTasks.includes(t.id)));
        setFilteredTasks(filteredTasks.filter(t => !selectedTasks.includes(t.id)));
        setSelectedTasks([]);
      } catch (error) {
        console.error('Failed to delete tasks:', error);
      }
    }
  };

  const taskStats = {
    total: filteredTasks.length,
    todo: filteredTasks.filter(t => t.status === 'todo').length,
    inProgress: filteredTasks.filter(t => t.status === 'in_progress').length,
    completed: filteredTasks.filter(t => t.status === 'done').length,
    overdue: filteredTasks.filter(t => 
      t.dueDate && new Date(t.dueDate) < new Date() && t.status !== 'done'
    ).length,
  };

  if (loading) {
    return <div className={styles.loading}>Loading tasks...</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Tasks</h1>
          <p className={styles.subtitle}>{taskStats.total} tasks total</p>
        </div>
        <div className={styles.actions}>
          <button
            className={styles.createButton}
            onClick={() => setIsCreateModalOpen(true)}
          >
            + New Task
          </button>
        </div>
      </div>

      <div className={styles.stats}>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>To Do</span>
          <span className={`${styles.statValue} ${styles.todo}`}>{taskStats.todo}</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>In Progress</span>
          <span className={`${styles.statValue} ${styles.progress}`}>{taskStats.inProgress}</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Completed</span>
          <span className={`${styles.statValue} ${styles.completed}`}>{taskStats.completed}</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Overdue</span>
          <span className={`${styles.statValue} ${styles.overdue}`}>{taskStats.overdue}</span>
        </div>
      </div>

      <TaskFilters onFilterChange={handleFilterChange} />

      {selectedTasks.length > 0 && (
        <div className={styles.bulkActions}>
          <span className={styles.selectedCount}>
            {selectedTasks.length} task{selectedTasks.length !== 1 ? 's' : ''} selected
          </span>
          <button className={styles.bulkButton} onClick={handleBulkDelete}>
            Delete Selected
          </button>
          <button 
            className={styles.bulkButton}
            onClick={() => setSelectedTasks([])}
          >
            Clear Selection
          </button>
        </div>
      )}

      <TaskListTable
        tasks={filteredTasks}
        selectedTasks={selectedTasks}
        onTaskClick={handleTaskClick}
        onTaskDelete={handleTaskDelete}
        onSelectionChange={setSelectedTasks}
      />

      {isCreateModalOpen && (
        <CreateTaskModal
          onClose={() => setIsCreateModalOpen(false)}
          onTaskCreated={handleTaskCreated}
        />
      )}
    </div>
  );
}

export default TaskListPage;