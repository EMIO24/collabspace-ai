import React from 'react';
import styles from './DueDateDisplay.module.css';

function DueDateDisplay({ dueDate, status }) {
  if (!dueDate) {
    return <span className={styles.notSet}>No due date</span>;
  }

  const date = new Date(dueDate);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(date);
  due.setHours(0, 0, 0, 0);

  const diffTime = due - today;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  let statusClass = '';
  let statusText = '';

  if (status === 'done') {
    statusClass = styles.completed;
    statusText = 'Completed';
  } else if (diffDays < 0) {
    statusClass = styles.overdue;
    statusText = `Overdue by ${Math.abs(diffDays)} day${Math.abs(diffDays) !== 1 ? 's' : ''}`;
  } else if (diffDays === 0) {
    statusClass = styles.today;
    statusText = 'Due today';
  } else if (diffDays === 1) {
    statusClass = styles.soon;
    statusText = 'Due tomorrow';
  } else if (diffDays <= 7) {
    statusClass = styles.soon;
    statusText = `Due in ${diffDays} days`;
  } else {
    statusClass = styles.upcoming;
    statusText = date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }

  return (
    <div className={`${styles.container} ${statusClass}`}>
      <svg className={styles.icon} viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
      </svg>
      <span className={styles.text}>{statusText}</span>
    </div>
  );
}

export default DueDateDisplay;