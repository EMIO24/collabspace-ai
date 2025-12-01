import React, { useState } from 'react';
import styles from './StatusBadge.module.css';

function StatusBadge({ status, editable = false, onChange }) {
  const [isOpen, setIsOpen] = useState(false);

  const statuses = [
    { value: 'todo', label: 'To Do', color: '#3b82f6' },
    { value: 'in_progress', label: 'In Progress', color: '#f59e0b' },
    { value: 'review', label: 'Review', color: '#8b5cf6' },
    { value: 'done', label: 'Done', color: '#10b981' },
  ];

  const currentStatus = statuses.find(s => s.value === status) || statuses[0];

  const handleChange = (newStatus) => {
    if (onChange) {
      onChange(newStatus);
    }
    setIsOpen(false);
  };

  if (!editable) {
    return (
      <span
        className={styles.badge}
        style={{ backgroundColor: currentStatus.color }}
      >
        {currentStatus.label}
      </span>
    );
  }

  return (
    <div className={styles.container}>
      <button
        className={styles.badge}
        style={{ backgroundColor: currentStatus.color }}
        onClick={() => setIsOpen(!isOpen)}
      >
        {currentStatus.label}
        <svg className={styles.icon} viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div className={styles.overlay} onClick={() => setIsOpen(false)} />
          <div className={styles.dropdown}>
            {statuses.map((s) => (
              <button
                key={s.value}
                className={`${styles.option} ${s.value === status ? styles.active : ''}`}
                onClick={() => handleChange(s.value)}
              >
                <div
                  className={styles.colorDot}
                  style={{ backgroundColor: s.color }}
                />
                {s.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default StatusBadge;