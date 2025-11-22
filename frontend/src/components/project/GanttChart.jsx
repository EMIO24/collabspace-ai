import React, { useMemo } from 'react';
import styles from './GanttChart.module.css';

function GanttChart({ tasks, viewMode = 'month' }) {
  const { timelineData, columns } = useMemo(() => {
    if (!tasks || tasks.length === 0) {
      return { timelineData: [], columns: [] };
    }

    // Find date range
    const dates = tasks
      .flatMap(task => [
        task.startDate ? new Date(task.startDate) : null,
        task.dueDate ? new Date(task.dueDate) : null,
      ])
      .filter(Boolean);

    if (dates.length === 0) {
      return { timelineData: [], columns: [] };
    }

    const minDate = new Date(Math.min(...dates));
    const maxDate = new Date(Math.max(...dates));

    // Generate timeline columns based on view mode
    const cols = [];
    let current = new Date(minDate);
    current.setDate(1); // Start of month

    while (current <= maxDate) {
      const label = current.toLocaleDateString('en-US', {
        month: 'short',
        year: viewMode === 'day' ? 'numeric' : undefined,
      });

      cols.push({
        date: new Date(current),
        label,
      });

      // Increment based on view mode
      if (viewMode === 'day') {
        current.setDate(current.getDate() + 1);
      } else if (viewMode === 'week') {
        current.setDate(current.getDate() + 7);
      } else {
        current.setMonth(current.getMonth() + 1);
      }
    }

    // Calculate task positions
    const timeline = tasks.map(task => {
      const start = task.startDate ? new Date(task.startDate) : minDate;
      const end = task.dueDate ? new Date(task.dueDate) : start;

      // Calculate position and width
      const totalDays = (maxDate - minDate) / (1000 * 60 * 60 * 24);
      const startOffset = (start - minDate) / (1000 * 60 * 60 * 24);
      const duration = Math.max((end - start) / (1000 * 60 * 60 * 24), 1);

      return {
        task,
        left: (startOffset / totalDays) * 100,
        width: (duration / totalDays) * 100,
        start,
        end,
      };
    });

    return { timelineData: timeline, columns: cols };
  }, [tasks, viewMode]);

  const getStatusColor = (status) => {
    const colors = {
      todo: '#3b82f6',
      in_progress: '#f59e0b',
      review: '#8b5cf6',
      done: '#10b981',
    };
    return colors[status] || '#6b7280';
  };

  if (timelineData.length === 0) {
    return <div className={styles.empty}>No tasks with dates to display</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.gantt}>
        {/* Task names column */}
        <div className={styles.taskNames}>
          <div className={styles.headerCell}>Tasks</div>
          {timelineData.map(({ task }) => (
            <div key={task.id} className={styles.taskName}>
              {task.title}
            </div>
          ))}
        </div>

        {/* Timeline */}
        <div className={styles.timeline}>
          {/* Timeline header */}
          <div className={styles.timelineHeader}>
            {columns.map((col, idx) => (
              <div key={idx} className={styles.timelineColumn}>
                {col.label}
              </div>
            ))}
          </div>

          {/* Task bars */}
          <div className={styles.chartArea}>
            {/* Grid lines */}
            {columns.map((col, idx) => (
              <div key={idx} className={styles.gridLine} />
            ))}

            {/* Task bars */}
            {timelineData.map(({ task, left, width }) => (
              <div
                key={task.id}
                className={styles.taskBar}
                style={{
                  left: `${left}%`,
                  width: `${Math.max(width, 2)}%`,
                  backgroundColor: getStatusColor(task.status),
                }}
                title={`${task.title} (${new Date(task.startDate).toLocaleDateString()} - ${new Date(task.dueDate).toLocaleDateString()})`}
              >
                <span className={styles.taskBarLabel}>{task.title}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default GanttChart;