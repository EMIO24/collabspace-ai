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
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { Plus, Filter, User, Archive, MoreHorizontal, PlusSquare, CheckSquare, ArrowRight } from 'lucide-react';
import { api } from '../../services/api';
import { toast } from 'react-hot-toast';
import KanbanColumn from './KanbanColumn';
import TaskCard from './TaskCard';
import CreateTaskModal from './CreateTaskModal';
import TaskDetailSlideOver from '../tasks/TaskDetailSlideOver'; 
import Button from '../../components/ui/Button/Button';
import styles from './KanbanBoard.module.css';

const COLUMNS = {
  todo: 'To Do',
  in_progress: 'In Progress',
  review: 'Review',
  done: 'Done' 
};

const KanbanBoard = ({ projectId }) => {
  const queryClient = useQueryClient();
  const [activeTask, setActiveTask] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [preselectedStatus, setPreselectedStatus] = useState('todo');

  // Filter State
  const [filterMyTasks, setFilterMyTasks] = useState(false);
  const [filterPriority, setFilterPriority] = useState('all');

  // Fetch Tasks
  const { data: rawData } = useQuery({
    queryKey: ['tasks', projectId],
    queryFn: async () => {
      const res = await api.get(`/tasks/tasks/?project=${projectId}`);
      return res.data;
    },
    enabled: !!projectId
  });

  // Fetch Current User for "My Tasks" filter
  const { data: user } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => (await api.get('/auth/profile/')).data
  });

  const tasks = useMemo(() => {
    if (!rawData) return [];
    const list = Array.isArray(rawData) ? rawData : (rawData.results || []);
    
    // --- CLIENT-SIDE FILTERING ---
    return list.filter(task => {
      // Filter out archived tasks from the board view
      if (task.status === 'archived') return false;
      
      if (filterMyTasks && user && String(task.assigned_to?.id) !== String(user.id)) return false;
      if (filterPriority !== 'all' && task.priority !== filterPriority) return false;
      return true;
    });
  }, [rawData, filterMyTasks, filterPriority, user]);

  const columns = useMemo(() => {
    const cols = { todo: [], in_progress: [], review: [], done: [] };
    tasks.forEach(task => {
      const status = task.status || 'todo';
      const key = status === 'completed' ? 'done' : status;
      if (cols[key]) cols[key].push(task);
      else if (cols.todo) cols.todo.push(task); // Fallback
    });
    return cols;
  }, [tasks]);

  // New State for Bulk Move Mode
  const [isBulkMode, setIsBulkMode] = useState(false);
  const [selectedCards, setSelectedCards] = useState(new Set());

  const toggleCardSelection = (id) => {
    const newSet = new Set(selectedCards);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedCards(newSet);
  };

  // Enhanced Bulk Move
  const bulkMoveMutation = useMutation({
    mutationFn: async (targetStatus) => {
      await Promise.all(Array.from(selectedCards).map(id => 
        api.patch(`/tasks/tasks/${id}/`, { status: targetStatus })
      ));
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['tasks', projectId]);
      setSelectedCards(new Set());
      setIsBulkMode(false);
      toast.success('Tasks moved successfully');
    }
  });

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  // --- MUTATIONS ---
  const moveTaskMutation = useMutation({
    mutationFn: ({ taskId, status }) => api.patch(`/tasks/tasks/${taskId}/`, { status }),
    onSuccess: () => queryClient.invalidateQueries(['tasks', projectId])
  });

  // Functional Archive Logic
  const archiveMutation = useMutation({
    mutationFn: async (taskIds) => {
      // Execute parallel updates
      await Promise.all(taskIds.map(id => api.patch(`/tasks/tasks/${id}/`, { status: 'archived' })));
    },
    onSuccess: () => {
      toast.success('Completed tasks archived');
      queryClient.invalidateQueries(['tasks', projectId]);
    },
    onError: () => toast.error('Failed to archive tasks')
  });

  const handleArchiveDone = () => {
    // Identify tasks in the 'done' column
    const doneTasks = columns.done.map(t => t.id);
    
    if (doneTasks.length === 0) {
      toast('No completed tasks to archive', { icon: 'ℹ️' });
      return;
    }

    if (confirm(`Archive ${doneTasks.length} completed tasks? This will hide them from the board.`)) {
      archiveMutation.mutate(doneTasks);
    }
  };

  const handleDragStart = (event) => setActiveTask(event.active.data.current);

  const handleDragEnd = (event) => {
    const { active, over } = event;
    setActiveTask(null);
    if (!over) return;

    const activeId = active.id;
    const overId = over.id;

    const findContainer = (id) => {
      if (id in COLUMNS) return id;
      return tasks.find(t => t.id === id)?.status === 'completed' ? 'done' : tasks.find(t => t.id === id)?.status;
    };

    let activeContainer = findContainer(activeId);
    let overContainer = findContainer(overId);
    
    if (activeContainer === 'completed') activeContainer = 'done';
    if (overContainer === 'completed') overContainer = 'done';

    if (!activeContainer || !overContainer || activeContainer === overContainer) return;

    moveTaskMutation.mutate({ taskId: activeId, status: overContainer });
  };

  const handleAddTask = (status = 'todo') => {
    setPreselectedStatus(status);
    setIsModalOpen(true);
  };

  return (
    <div className={styles.container}>
      
      {/* --- TOOLBAR & FILTERS --- */}
      <div className={styles.toolbar}>
        <div className={styles.filterGroup}>
           <button 
             className={`${styles.filterBtn} ${filterMyTasks ? styles.activeFilter : ''}`}
             onClick={() => setFilterMyTasks(!filterMyTasks)}
           >
             <User size={14} /> My Tasks
           </button>

           <select 
              className={`${styles.filterBtn} ${filterPriority !== 'all' ? styles.activeFilter : ''}`}
              value={filterPriority}
              onChange={(e) => setFilterPriority(e.target.value)}
           >
              <option value="all">All Priorities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="urgent">Urgent</option>
           </select>
        </div>

        <div className={styles.boardActions}>
           {isBulkMode ? (
             <div className="flex items-center gap-2 bg-blue-50 p-1 rounded-lg border border-blue-100">
                <span className="text-sm font-bold text-blue-600 px-2">{selectedCards.size} Selected</span>
                <button className={styles.actionBtn} onClick={() => bulkMoveMutation.mutate('done')}>
                   Move to Done
                </button>
                <button className={styles.secondaryBtn} onClick={() => setIsBulkMode(false)}>Cancel</button>
             </div>
           ) : (
             <button className={styles.secondaryBtn} onClick={() => setIsBulkMode(true)}>
               <CheckSquare size={16} className="mr-2" /> Select Tasks
             </button>
           )}

           {/* Wired up Archive Button */}
           <button 
             className={`${styles.actionBtn} ${styles.secondaryBtn}`}
             onClick={handleArchiveDone}
             disabled={archiveMutation.isPending}
           >
             <Archive size={16} /> {archiveMutation.isPending ? 'Archiving...' : 'Archive Done'}
           </button>
           <button className={styles.actionBtn} onClick={() => handleAddTask('todo')}>
             <PlusSquare size={16} /> New Task
           </button>
        </div>
      </div>

      {/* --- BOARD --- */}
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
              onTaskClick={(taskId) => {
                 if (isBulkMode) toggleCardSelection(taskId);
                 else setSelectedTaskId(taskId);
              }}
              onAddTask={handleAddTask}
              // Pass selection state down to card (need to update Card component to accept these)
              isBulkMode={isBulkMode}
              selectedIds={selectedCards}
            />
          ))}
          
          {/* New Column Placeholder */}
          <div 
            className={styles.newColumnBtn}
            onClick={() => toast('Custom columns require Admin plan', { icon: '🔒' })}
          >
             + Add Column
          </div>
        </div>

        <DragOverlay>
          {activeTask ? <TaskCard task={activeTask} /> : null}
        </DragOverlay>
      </DndContext>

      {isModalOpen && (
        <CreateTaskModal 
          projectId={projectId} 
          initialStatus={preselectedStatus}
          onClose={() => setIsModalOpen(false)} 
        />
      )}

      {selectedTaskId && (
        <TaskDetailSlideOver 
           taskId={selectedTaskId} 
           onClose={() => setSelectedTaskId(null)} 
        />
      )}
    </div>
  );
};

export default KanbanBoard;