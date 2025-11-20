import React, { useState, useRef, useEffect } from 'react';
import styles from './UserDropdown.module.css';
import { useSelector, useDispatch } from 'react-redux';
import { logout } from '@store/slices/authSlice';
import { useNavigate } from 'react-router-dom';

export default function UserDropdown() {
  const user = useSelector((s) => s.auth.user);
  const [open, setOpen] = useState(false);
  const ref = useRef();
  const dispatch = useDispatch();
  const nav = useNavigate();

  useEffect(() => {
    function onDoc(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('click', onDoc);
    return () => document.removeEventListener('click', onDoc);
  }, []);

  const doLogout = async () => {
    await dispatch(logout());
    nav('/login');
  };

  return (
    <div className={styles.wrap} ref={ref}>
      <button className={styles.trigger} onClick={() => setOpen((v) => !v)} aria-haspopup="true">
        <img src={user?.avatar || '/avatar-placeholder.png'} alt="you" className={styles.avatar} />
      </button>

      {open && (
        <div className={styles.menu} role="menu">
          <div className={styles.header}>
            <div className={styles.name}>{user?.first_name} {user?.last_name}</div>
            <div className={styles.email}>{user?.email}</div>
          </div>
          <button className={styles.item} onClick={() => { nav('/settings'); setOpen(false); }}>Settings</button>
          <button className={styles.item} onClick={() => { nav('/profile'); setOpen(false); }}>Profile</button>
          <div className={styles.sep} />
          <button className={styles.itemDanger} onClick={doLogout}>Sign out</button>
        </div>
      )}
    </div>
  );
}
