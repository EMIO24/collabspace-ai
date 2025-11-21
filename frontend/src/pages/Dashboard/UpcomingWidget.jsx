import React from 'react';
import { Link } from 'react-router-dom';
import Widget from '../common/Widget';
import styles from './UpcomingWidget.module.css';

const mockUpcoming = [
  { id: 1, type: 'Meeting', title: 'Sprint Planning', date: 'Fri, Nov 22' },
  { id: 2, type: 'Deadline', title: 'UI/UX Mockups Final', date: 'Mon, Nov 25' },
  { id: 3, type: 'Event', title: 'Team Lunch', date: 'Fri, Nov 29' },
];

export default function UpcomingWidget() {
  const loading = false;

  return (
    <Widget title="Upcoming" action={<Link to="/calendar">Calendar</Link>}>
      {loading ? (
        <div className={styles.loading}>Loading events...</div>
      ) : (
        <ul className={styles.eventList}>
          {mockUpcoming.map(item => (
            <li key={item.id} className={styles.eventItem}>
              <div className={`${styles.type} ${styles[item.type.toLowerCase()]}`}>{item.type}</div>
              <div className={styles.details}>
                <div className={styles.title}>{item.title}</div>
                <div className={styles.date}>{item.date}</div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Widget>
  );
}