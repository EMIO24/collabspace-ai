import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import { toast } from 'react-hot-toast';
import { 
  Plus, Filter, Download, LayoutList, KanbanSquare, 
  CheckSquare, Trash2, ArrowUpDown, Briefcase, User, Calendar
} from 'lucide-react';
import Badge from '../../components/ui/Badge/Badge';
import Avatar from '../../components/ui/Avatar/Avatar';
import Button from '../../components/ui/Button/Button';
import CreateTaskModal from '../kanban/CreateTaskModal';
import TaskDetailSlideOver from './TaskDetailSlideOver';
import styles from './MyTasksPage.module.css';

const PRIORITY_COLORS = {
  low: 'info',
  medium: 'warning',
  high: 'danger',
  urgent: 'purple'
};

const MyTasksPage = () => {
  const queryClient = useQueryClient();
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [groupBy, setGroupBy] = useState('none'); // none, project, status, priority
  const [sortConfig, setSortConfig] = useState({ key: 'due_date', direction: 'asc' });
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  // 1. Fetch User
  const { data: user } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      try { return (await api.get('/auth/profile/')).data; } catch { return null; }
    }
  });

  // 2. Fetch Tasks
  const { data: rawData, isLoading } = useQuery({
    queryKey: ['myTasks', user?.id, filterStatus, filterPriority],
    queryFn: async () => {
      if (!user?.id) return [];
      const params = new URLSearchParams({ assigned_to: user.id });
      if (filterStatus) params.append('status', filterStatus);
      if (filterPriority) params.append('priority', filterPriority);
      try {
        const res = await api.get(`/tasks/tasks/?${params.toString()}`);
        return res.data;
      } catch { return []; }
    },
    enabled: !!user?.id
  });

  // 3. Normalize, Sort & Group Data
  const tasks = useMemo(() => {
    let list = [];
    if (Array.isArray(rawData)) list = rawData;
    else if (rawData?.results) list = rawData.results;

    // Sorting
    list.sort((a, b) => {
      let aVal = a[sortConfig.key] || '';
      let bVal = b[sortConfig.key] || '';
      if (a[sortConfig.key] === null) aVal = 'z'; // Push nulls to end
      
      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });

    return list;
  }, [rawData, sortConfig]);

  const groupedTasks = useMemo(() => {
    if (groupBy === 'none') return { 'All Tasks': tasks };
    
    return tasks.reduce((acc, task) => {
      const key = task[groupBy] || 'Unassigned';
      // Handle object grouping (like project object)
      const groupName = typeof key === 'object' ? (key.name || 'Unknown') : key;
      
      if (!acc[groupName]) acc[groupName] = [];
      acc[groupName].push(task);
      return acc;
    }, {});
  }, [tasks, groupBy]);

  // --- ACTIONS ---
  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(new Set(tasks.map(t => t.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleSelectRow = (id) => {
    const newSet = new Set(selectedIds);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedIds(newSet);
  };

  // Bulk Mutations
  const bulkUpdateMutation = useMutation({
    mutationFn: async ({ ids, payload }) => {
      await Promise.all(ids.map(id => api.patch(`/tasks/tasks/${id}/`, payload)));
    },
    onSuccess: () => {
      toast.success(`Updated ${selectedIds.size} tasks`);
      queryClient.invalidateQueries(['myTasks']);
      setSelectedIds(new Set());
    }
  });

  const bulkDeleteMutation = useMutation({
    mutationFn: async (ids) => {
      await Promise.all(ids.map(id => api.delete(`/tasks/tasks/${id}/`)));
    },
    onSuccess: () => {
      toast.success(`Deleted ${selectedIds.size} tasks`);
      queryClient.invalidateQueries(['myTasks']);
      setSelectedIds(new Set());
    }
  });

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div>
           <h1 className={styles.title}>My Tasks</h1>
           <p className="text-gray-500 mt-1">Manage your daily priorities</p>
        </div>
        <div className={styles.controls}>
           <div className={styles.viewToggle}>
              <button className={`${styles.viewBtn} ${styles.activeView}`}><LayoutList size={18}/></button>
              <button className={styles.viewBtn}><KanbanSquare size={18}/></button>
           </div>
           <button className={styles.iconBtn} title="Export CSV"><Download size={18} /></button>
           <Button onClick={() => setIsCreateOpen(true)}>
             <Plus size={18} className="mr-2" /> New Task
           </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className={styles.filterBar}>
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-600 mr-2">
           <Filter size={16} /> Filters:
        </div>
        <select className={styles.select} value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">Status: All</option>
          <option value="todo">To Do</option>
          <option value="in_progress">In Progress</option>
          <option value="done">Done</option>
        </select>

        <select className={styles.select} value={filterPriority} onChange={(e) => setFilterPriority(e.target.value)}>
          <option value="">Priority: All</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <div className="w-px h-6 bg-gray-200 mx-2" />

        <div className="flex items-center gap-2 text-sm font-semibold text-gray-600 mr-2">
           Group By:
        </div>
        <select className={styles.select} value={groupBy} onChange={(e) => setGroupBy(e.target.value)}>
          <option value="none">None</option>
          <option value="project_name">Project</option>
          <option value="status">Status</option>
          <option value="priority">Priority</option>
        </select>
      </div>

      {/* Data Grid */}
      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th style={{ width: '40px' }}>
                 <input 
                    type="checkbox" 
                    className={styles.checkbox}
                    onChange={handleSelectAll}
                    checked={tasks.length > 0 && selectedIds.size === tasks.length}
                 />
              </th>
              <th onClick={() => handleSort('title')}>Name <ArrowUpDown size={12} className="inline ml-1"/></th>
              <th onClick={() => handleSort('status')}>Status</th>
              <th onClick={() => handleSort('priority')}>Priority</th>
              <th onClick={() => handleSort('project_name')}>Project</th>
              <th onClick={() => handleSort('due_date')}>Due Date</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(groupedTasks).map(([group, groupTasks]) => (
              <React.Fragment key={group}>
                {groupBy !== 'none' && (
                  <tr>
                    <td colSpan="7" className={styles.groupHeader}>{group} ({groupTasks.length})</td>
                  </tr>
                )}
                {groupTasks.map(task => (
                  <tr 
                    key={task.id} 
                    className={`${styles.row} ${selectedIds.has(task.id) ? styles.selectedRow : ''}`}
                    onClick={() => setSelectedTaskId(task.id)}
                  >
                    <td onClick={(e) => e.stopPropagation()}>
                       <input 
                          type="checkbox" 
                          className={styles.checkbox}
                          checked={selectedIds.has(task.id)}
                          onChange={() => handleSelectRow(task.id)}
                       />
                    </td>
                    <td>
                      <span className={styles.taskTitle}>{task.title}</span>
                    </td>
                    <td>
                      <Badge variant="gray">
                        {task.status === 'done' ? 'Done' : task.status.replace('_', ' ')}
                      </Badge>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                         <div className={`w-2 h-2 rounded-full bg-${PRIORITY_COLORS[task.priority]?.replace('info', 'blue-500').replace('warning','yellow-500').replace('danger','red-500')}`} />
                         <span className="capitalize text-sm">{task.priority}</span>
                      </div>
                    </td>
                    <td>
                       <span className={styles.projectName}>{task.project_name || '-'}</span>
                    </td>
                    <td>
                      {task.due_date ? new Date(task.due_date).toLocaleDateString() : '-'}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                       {/* Inline Actions could go here */}
                    </td>
                  </tr>
                ))}
              </React.Fragment>
            ))}
            {!tasks.length && !isLoading && (
               <tr><td colSpan="7" className="text-center p-10 text-gray-400">No tasks found.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Bulk Action Bar */}
      {selectedIds.size > 0 && (
        <div className={styles.bulkBar}>
           <div className={styles.bulkCount}>
              <CheckSquare size={18} /> {selectedIds.size} Selected
           </div>
           <div className={styles.bulkActions}>
              <button 
                 className={styles.bulkBtn}
                 onClick={() => bulkUpdateMutation.mutate({ ids: Array.from(selectedIds), payload: { status: 'done' } })}
              >
                 Mark Complete
              </button>
              
              {/* Priority Dropdown Mock for Bulk */}
              <button 
                 className={styles.bulkBtn}
                 onClick={() => bulkUpdateMutation.mutate({ ids: Array.from(selectedIds), payload: { priority: 'high' } })}
              >
                 Set High Priority
              </button>

              <button 
                 className={`${styles.bulkBtn} ${styles.deleteBtn}`}
                 onClick={() => {
                    if(confirm('Delete selected tasks?')) bulkDeleteMutation.mutate(Array.from(selectedIds));
                 }}
              >
                 <Trash2 size={16} /> Delete
              </button>
           </div>
        </div>
      )}

      {selectedTaskId && <TaskDetailSlideOver taskId={selectedTaskId} onClose={() => setSelectedTaskId(null)} />}
      {isCreateOpen && <CreateTaskModal projectId={null} onClose={() => setIsCreateOpen(false)} />}
    </div>
  );
};

export default MyTasksPage;