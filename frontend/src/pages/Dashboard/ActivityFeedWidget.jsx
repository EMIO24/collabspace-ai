import React from 'react';
import Widget from '../common/Widget';
import styles from './ActivityFeedWidget.module.css';

const mockActivity = [
  { id: 1, user: 'John D.', action: 'assigned task "Fix Auth Bug"', time: '2 mins ago' },
  { id: 2, user: 'Jane S.', action: 'completed task "Design Review"', time: '1 hour ago' },
  { id: 3, user: 'Collab Bot', action: 'added deadline for project "Relaunch"', time: '2 hours ago' },
  { id: 4, user: 'Alex P.', action: 'commented on task "Refactor API"', time: 'Yesterday' },
];

export default function ActivityFeedWidget() {
  const loading = false;
  const error = null;

  return (
    <Widget title="Activity Feed" className={styles.activityWidget}>
      {loading ? (
        <div className={styles.loading}>Loading activity...</div>
      ) : error ? (
        <div className={styles.error}>{error}</div>
      ) : (
        <ul className={styles.feed}>
          {mockActivity.map(item => (
            <li key={item.id} className={styles.feedItem}>
              <div className={styles.user}>{item.user}</div>
              <div className={styles.action}>{item.action}</div>
              <div className={styles.time}>{item.time}</div>
            </li>
          ))}
        </ul>
      )}
    </Widget>
  );
}