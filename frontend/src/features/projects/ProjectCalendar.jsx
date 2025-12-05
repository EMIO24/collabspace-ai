import React, { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { api } from '../../services/api';
import TaskDetailSlideOver from '../tasks/TaskDetailSlideOver';
import styles from './ProjectCalendar.module.css';

const ProjectCalendar = () => {
  const { id } = useParams();
  const [selectedTaskId, setSelectedTaskId] = useState(null);

  // 1. Fetch Raw Data
  const { data: rawData, isLoading } = useQuery({
    queryKey: ['tasks', id],
    queryFn: async () => {
      const res = await api.get(`/tasks/tasks/?project=${id}`);
      return res.data;
    },
    enabled: !!id
  });

  // 2. Normalize Data (Safety Check)
  const tasks = useMemo(() => {
    if (!rawData) return [];
    if (Array.isArray(rawData)) return rawData;
    if (rawData.results && Array.isArray(rawData.results)) return rawData.results;
    return [];
  }, [rawData]);

  // 3. Map normalized tasks to Calendar Events
  const events = tasks.map(task => ({
    id: task.id,
    title: task.title,
    start: task.due_date || task.created_at, // Fallback if no due date
    className: `event-${task.priority || 'low'}`, // For CSS styling
    extendedProps: { ...task }
  }));

  const handleEventClick = (info) => {
    setSelectedTaskId(info.event.id);
  };

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading calendar...</div>;

  return (
    <>
      <div className={styles.container}>
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek'
          }}
          events={events}
          eventClick={handleEventClick}
          height="100%"
          dayMaxEvents={true}
        />
      </div>

      <TaskDetailSlideOver 
        taskId={selectedTaskId} 
        onClose={() => setSelectedTaskId(null)} 
      />
    </>
  );
};

export default ProjectCalendar;