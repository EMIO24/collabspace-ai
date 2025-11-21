import React from 'react';
import Widget from '../common/Widget';
import styles from './TeamMembersWidget.module.css';

const mockMembers = [
  { id: 1, name: 'Ava Chen', role: 'Design Lead', status: 'Online' },
  { id: 2, name: 'Ben Lee', role: 'Frontend Dev', status: 'In Meeting' },
  { id: 3, name: 'Chris P.', role: 'Backend Engineer', status: 'Offline' },
];

export default function TeamMembersWidget() {
  const loading = false;

  return (
    <Widget title="Team Members">
      {loading ? (
        <div className={styles.loading}>Loading team...</div>
      ) : (
        <ul className={styles.memberList}>
          {mockMembers.map(m => (
            <li key={m.id} className={styles.memberItem}>
              <div className={styles.avatar}>
                {m.name.charAt(0)}
              </div>
              <div className={styles.info}>
                <div className={styles.name}>{m.name}</div>
                <div className={styles.role}>{m.role}</div>
              </div>
              <div className={`${styles.status} ${styles[m.status.replace(/\s/g, '').toLowerCase()]}`}>
                {m.status}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Widget>
  );
}