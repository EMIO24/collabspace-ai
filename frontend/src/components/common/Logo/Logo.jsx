import React from 'react';
import styles from './Logo.module.css';

export default function Logo() {
  return (
    <div className={styles.logo}>
      <div className={styles.mark}>CS</div>
      <div className={styles.text}>CollabSpace</div>
    </div>
  );
}
