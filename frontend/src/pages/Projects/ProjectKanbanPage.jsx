import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable } from 'react-beautiful-dnd';
import { getTasks, updateTask, createTask } from '../../api/tasks';
import KanbanColumn from '../../components/project/KanbanColumn';
import styles from './ProjectKanbanPage.module.css';

function ProjectKanbanPage() {
  const [columns, setColumns] = useState({
    todo: { id: 'todo', title: 'To Do', tasks: [] },
    inProgress: { id: 'inProgress', title: 'In Progress', tasks: [] },
    review: { id: 'review', title: 'Review', tasks: [] },
    done: { id: 'done', title: 'Done', tasks: [] },
  });
  const [isAddingTask, setIsAddingTask] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [selectedColumn, setSelectedColumn] = useState('todo');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const response = await getTasks();
      const tasks = response.data;

      const groupedTasks = {
        todo: { ...columns.todo, tasks: tasks.filter(t => t.status === 'todo') },
        inProgress: { ...columns.inProgress, tasks: tasks.filter(t => t.status === 'in_progress') },
        review: { ...columns.review, tasks: tasks.filter(t => t.status === 'review') },
        done: { ...columns.done, tasks: tasks.filter(t => t.status === 'done') },
      };

      setColumns(groupedTasks);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const onDragEnd = async (result) => {
    const { source, destination, draggableId } = result;

    if (!destination) return;

    if (
      source.droppableId === destination.droppableId &&
      source.index === destination.index
    ) {
      return;
    }

    const sourceColumn = columns[source.droppableId];
    const destColumn = columns[destination.droppableId];
    const sourceTasks = [...sourceColumn.tasks];
    const destTasks = source.droppableId === destination.droppableId
      ? sourceTasks
      : [...destColumn.tasks];

    const [movedTask] = sourceTasks.splice(source.index, 1);
    destTasks.splice(destination.index, 0, movedTask);

    setColumns({
      ...columns,
      [source.droppableId]: {
        ...sourceColumn,
        tasks: sourceTasks,
      },
      [destination.droppableId]: {
        ...destColumn,
        tasks: destTasks,
      },
    });

    // Update task status on backend
    try {
      const newStatus = destination.droppableId.replace(/([A-Z])/g, '_$1').toLowerCase();
      await updateTask(draggableId, { status: newStatus });
    } catch (error) {
      console.error('Failed to update task:', error);
      // Revert on error
      loadTasks();
    }
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    try {
      const newTask = {
        title: newTaskTitle,
        status: selectedColumn.replace(/([A-Z])/g, '_$1').toLowerCase(),
        description: '',
      };

      const response = await createTask(newTask);
      const createdTask = response.data;

      setColumns({
        ...columns,
        [selectedColumn]: {
          ...columns[selectedColumn],
          tasks: [...columns[selectedColumn].tasks, createdTask],
        },
      });

      setNewTaskTitle('');
      setIsAddingTask(false);
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  if (loading) {
    return <div className={styles.loading}>Loading board...</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Project Board</h1>
          <p className={styles.subtitle}>Drag and drop tasks to update their status</p>
        </div>
        <button className={styles.addButton} onClick={() => setIsAddingTask(true)}>
          + Add Task
        </button>
      </div>

      {isAddingTask && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h2 className={styles.modalTitle}>Add New Task</h2>
            <form onSubmit={handleAddTask}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Task Title</label>
                <input
                  type="text"
                  className={styles.input}
                  value={newTaskTitle}
                  onChange={(e) => setNewTaskTitle(e.target.value)}
                  placeholder="Enter task title"
                  autoFocus
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Column</label>
                <select
                  className={styles.select}
                  value={selectedColumn}
                  onChange={(e) => setSelectedColumn(e.target.value)}
                >
                  <option value="todo">To Do</option>
                  <option value="inProgress">In Progress</option>
                  <option value="review">Review</option>
                  <option value="done">Done</option>
                </select>
              </div>
              <div className={styles.modalActions}>
                <button
                  type="button"
                  className={styles.cancelButton}
                  onClick={() => {
                    setIsAddingTask(false);
                    setNewTaskTitle('');
                  }}
                >
                  Cancel
                </button>
                <button type="submit" className={styles.submitButton}>
                  Add Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <DragDropContext onDragEnd={onDragEnd}>
        <div className={styles.board}>
          {Object.values(columns).map((column) => (
            <KanbanColumn key={column.id} column={column} />
          ))}
        </div>
      </DragDropContext>
    </div>
  );
}

export default ProjectKanbanPage;