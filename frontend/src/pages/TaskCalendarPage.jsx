import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { api } from '../services/api';
import { toast } from 'react-hot-toast';
import { Filter, Plus } from 'lucide-react';
import Button from '../components/ui/Button/Button';
import CreateTaskModal from '../features/kanban/CreateTaskModal';
import TaskDetailSlideOver from '../features/tasks/TaskDetailSlideOver';
import styles from './TaskCalendarPage.module.css';

const TaskCalendarPage = () => {
  const queryClient = useQueryClient();
  const [filterPriority, setFilterPriority] = useState('all');
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);

  // 1. Fetch Tasks (Global)
  const { data: rawTasks, isLoading } = useQuery({
    queryKey: ['taskCalendar', filterPriority],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filterPriority !== 'all') params.append('priority', filterPriority);
      
      // Fetch tasks (assuming /tasks/tasks/ returns all visible to user)
      const res = await api.get(`/tasks/tasks/?${params.toString()}`);
      return res.data;
    }
  });

  const tasks = useMemo(() => {
    if (!rawTasks) return [];
    if (Array.isArray(rawTasks)) return rawTasks;
    return rawTasks.results || [];
  }, [rawTasks]);

  // 2. Map to Calendar Events
  const events = useMemo(() => tasks.map(task => ({
    id: String(task.id),
    title: task.title,
    start: task.due_date, // Must be YYYY-MM-DD or ISO
    // Default to 'low' if priority missing
    classNames: [`event-${task.priority || 'low'}`], 
    extendedProps: { ...task }
  })), [tasks]);

  // 3. Mutations
  const rescheduleMutation = useMutation({
    mutationFn: ({ id, date }) => api.patch(`/tasks/tasks/${id}/`, { due_date: date }),
    onSuccess: () => {
      toast.success('Task rescheduled');
      queryClient.invalidateQueries(['taskCalendar']);
      queryClient.invalidateQueries(['myTasks']);
    },
    onError: () => {
      toast.error('Failed to reschedule');
      queryClient.invalidateQueries(['taskCalendar']); // Revert UI
    }
  });

  // Handlers
  const handleEventClick = (info) => {
    setSelectedTaskId(info.event.id);
  };

  const handleDateClick = (info) => {
    setSelectedDate(info.dateStr);
    setIsCreateOpen(true);
  };

  const handleEventDrop = (info) => {
    if (!confirm(`Reschedule "${info.event.title}" to ${info.event.start.toLocaleDateString()}?`)) {
      info.revert();
      return;
    }
    // FullCalendar returns Date object, format to YYYY-MM-DD for API
    const newDate = info.event.start.toISOString().split('T')[0];
    rescheduleMutation.mutate({ id: info.event.id, date: newDate });
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Calendar</h1>
        <Button onClick={() => { setSelectedDate(new Date().toISOString().split('T')[0]); setIsCreateOpen(true); }}>
          <Plus size={18} className="mr-2" /> New Task
        </Button>
      </div>

      {/* Filter Toolbar */}
      <div className={styles.toolbar}>
        <div className="flex items-center gap-2 text-sm font-bold text-gray-500 uppercase tracking-wider">
          <Filter size={16} /> Filters
        </div>
        
        <select 
          className={styles.select}
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value)}
        >
          <option value="all">All Priorities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="urgent">Urgent</option>
        </select>
        
        {/* Add more filters here (Assignee, Project) if needed */}
      </div>

      {/* Calendar */}
      <div className={styles.calendarWrapper}>
        {isLoading ? (
          <div className="h-full flex items-center justify-center text-gray-400">Loading calendar...</div>
        ) : (
          <FullCalendar
            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
            initialView="dayGridMonth"
            headerToolbar={{
              left: 'prev,next today',
              center: 'title',
              right: 'dayGridMonth,timeGridWeek'
            }}
            events={events}
            editable={true}
            droppable={true}
            eventDrop={handleEventDrop}
            eventClick={handleEventClick}
            dateClick={handleDateClick}
            height="100%"
            dayMaxEvents={3}
            moreLinkClick="popover"
          />
        )}
      </div>

      {/* Modals */}
      {isCreateOpen && (
        <CreateTaskModal 
          initialDate={selectedDate} 
          onClose={() => setIsCreateOpen(false)} 
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

export default TaskCalendarPage;