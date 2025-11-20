import React from 'react';
import styles from './AuthLayout.module.css';

export default function AuthLayout({ children, title }) {
  return (
    <div className={styles.container}>
      <div className={styles.brand}>CollabSpace</div>
      <div className={styles.inner}>
        <h2 className={styles.title}>{title}</h2>
        <div className={styles.card}>{children}</div>
      </div>
      <footer className={styles.footer}>© {new Date().getFullYear()} CollabSpace</footer>
    </div>
  );
}
