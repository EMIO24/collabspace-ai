import React, { useState } from 'react';
import styles from './PriorityBadge.module.css';

function PriorityBadge({ priority, editable = false, onChange }) {
  const [isOpen, setIsOpen] = useState(false);

  const priorities = [
    { value: 'low', label: 'Low', color: '#10b981' },
    { value: 'medium', label: 'Medium', color: '#f59e0b' },
    { value: 'high', label: 'High', color: '#ef4444' },
  ];

  const currentPriority = priorities.find(p => p.value === priority) || priorities[1];

  const handleChange = (newPriority) => {
    if (onChange) {
      onChange(newPriority);
    }
    setIsOpen(false);
  };

  if (!editable) {
    return (
      <span
        className={styles.badge}
        style={{ backgroundColor: currentPriority.color }}
      >
        {currentPriority.label}
      </span>
    );
  }

  return (
    <div className={styles.container}>
      <button
        className={styles.badge}
        style={{ backgroundColor: currentPriority.color }}
        onClick={() => setIsOpen(!isOpen)}
      >
        {currentPriority.label}
        <svg className={styles.icon} viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div className={styles.overlay} onClick={() => setIsOpen(false)} />
          <div className={styles.dropdown}>
            {priorities.map((p) => (
              <button
                key={p.value}
                className={`${styles.option} ${p.value === priority ? styles.active : ''}`}
                onClick={() => handleChange(p.value)}
              >
                <div
                  className={styles.colorDot}
                  style={{ backgroundColor: p.color }}
                />
                {p.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default PriorityBadge;