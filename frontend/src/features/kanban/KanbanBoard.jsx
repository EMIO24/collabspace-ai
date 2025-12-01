import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { sortableKeyboardCoordinates, arrayMove } from '@dnd-kit/sortable';
import { Plus } from 'lucide-react';
import { api } from '../../services/api';
import KanbanColumn from './KanbanColumn';
import TaskCard from './TaskCard';
import CreateTaskModal from './CreateTaskModal';
import Button from '../../components/ui/Button/Button';
import styles from './KanbanBoard.module.css';

const COLUMNS = {
  todo: 'To Do',
  in_progress: 'In Progress',
  review: 'Review',
  completed: 'Completed'
};

const KanbanBoard = ({ projectId }) => {
  const queryClient = useQueryClient();
  const [activeTask, setActiveTask] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Fetch Tasks
  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks', projectId],
    queryFn: async () => {
      const res = await api.get(`/tasks/tasks/?project=${projectId}`);
      return res.data;
    },
    enabled: !!projectId
  });

  // Organize tasks by column
  const columns = useMemo(() => {
    const cols = { todo: [], in_progress: [], review: [], completed: [] };
    tasks.forEach(task => {
      if (cols[task.status]) {
        cols[task.status].push(task);
      }
    });
    // Sort by column_order within columns if API provides it, 
    // otherwise they just pile up. Ideally API sorts.
    return cols;
  }, [tasks]);

  // Drag Sensors
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  // Mutation for API Update
  const moveTaskMutation = useMutation({
    mutationFn: ({ taskId, status, order }) => 
      api.put(`/tasks/tasks/${taskId}/`, { status, column_order: order }),
    onError: () => {
      // Revert on error (could use queryClient.setQueryData to revert)
      queryClient.invalidateQueries(['tasks', projectId]);
    }
  });

  const handleDragStart = (event) => {
    setActiveTask(event.active.data.current);
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    setActiveTask(null);

    if (!over) return;

    const activeId = active.id;
    const overId = over.id;

    // Find source and destination containers
    // Note: over.id could be a task ID OR a column ID (if dropped on empty column)
    const findContainer = (id) => {
      if (id in COLUMNS) return id;
      return tasks.find(t => t.id === id)?.status;
    };

    const activeContainer = findContainer(activeId);
    const overContainer = findContainer(overId);

    if (!activeContainer || !overContainer || !projectId) return;

    // Optimistic Update
    if (activeContainer !== overContainer || activeId !== overId) {
      // Calculate new index
      // If dropping on a container (empty column), index is length of items
      // If dropping on a task, index is that task's index
      
      const newStatus = overContainer;
      
      // Perform optimistic UI update logic here or simply invalidate
      // For high fidelity, we manually manipulate the cache
      
      queryClient.setQueryData(['tasks', projectId], (oldTasks) => {
        const newTasks = [...oldTasks];
        const taskIndex = newTasks.findIndex(t => t.id === activeId);
        
        if (taskIndex !== -1) {
            newTasks[taskIndex] = { ...newTasks[taskIndex], status: newStatus };
            // In a real implementation, we would also calculate the exact `column_order`
            // based on `overId` index and shift array elements. 
        }
        return newTasks;
      });

      // Send to API
      // We send a simplified index update for demo purposes
      moveTaskMutation.mutate({ 
        taskId: activeId, 
        status: newStatus,
        order: 0 // Backend handles precise reordering in robust apps
      });
    }
  };

  return (
    <div>
      <div className={styles.controls}>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus size={18} /> Add Task
        </Button>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className={styles.boardContainer}>
          {Object.entries(COLUMNS).map(([statusKey, title]) => (
            <KanbanColumn
              key={statusKey}
              id={statusKey}
              title={title}
              tasks={columns[statusKey]}
            />
          ))}
        </div>

        <DragOverlay>
          {activeTask ? <TaskCard task={activeTask} /> : null}
        </DragOverlay>
      </DndContext>

      {isModalOpen && (
        <CreateTaskModal 
          projectId={projectId} 
          onClose={() => setIsModalOpen(false)} 
        />
      )}
    </div>
  );
};

export default KanbanBoard;