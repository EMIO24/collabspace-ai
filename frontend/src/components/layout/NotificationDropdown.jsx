import React, { useState, useRef, useEffect } from 'react';
import styles from './NotificationDropdown.module.css';
import { useSelector, useDispatch } from 'react-redux';
import { removeNotification } from '@store/slices/notificationSlice';
import PropTypes from 'prop-types';

export default function NotificationDropdown() {
  const notifications = useSelector((s) => s.notification.list || []);
  const [open, setOpen] = useState(false);
  const ref = useRef();
  const dispatch = useDispatch();

  useEffect(() => {
    function onDoc(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('click', onDoc);
    return () => document.removeEventListener('click', onDoc);
  }, []);

  return (
    <div className={styles.wrap} ref={ref}>
      <button className={styles.trigger} onClick={() => setOpen((v) => !v)} aria-label="Notifications" title="Notifications">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0 1 18 14.158V11a6 6 0 1 0-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h11z"/></svg>
        {notifications.length > 0 && <span className={styles.badge}>{notifications.length}</span>}
      </button>

      {open && (
        <div className={styles.menu}>
          <div className={styles.header}>Notifications</div>
          <ul className={styles.list}>
            {notifications.length === 0 && <li className={styles.empty}>No new notifications</li>}
            {notifications.map((n) => (
              <li key={n.id} className={styles.item}>
                <div className={styles.msg}>{n.message}</div>
                <button className={styles.dismiss} onClick={() => dispatch(removeNotification(n.id))}>Dismiss</button>
              </li>
            ))}
          </ul>
          <div className={styles.footer}><a href="/notifications">View all</a></div>
        </div>
      )}
    </div>
  );
}

NotificationDropdown.propTypes = {
  // none
};
