import React from 'react';
import styles from './LoadingScreen.module.css';

const LoadingScreen = ({ message = 'Initializing CollabSpace...' }) => {
  return (
    <div className={styles.container}>
      <div className={styles.spinner} />
      <p className={styles.text}>{message}</p>
    </div>
  );
};

export default LoadingScreen;