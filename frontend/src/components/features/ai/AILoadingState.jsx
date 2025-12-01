import React from 'react';
import PropTypes from 'prop-types';
import styles from './AILoadingState.module.css';

function AILoadingState({ message, fullScreen }) {
  const content = (
    <div className={styles.content}>
      <div className={styles.brain}>
        <svg viewBox="0 0 100 100" className={styles.brainIcon}>
          <circle cx="50" cy="50" r="40" className={styles.circle1} />
          <circle cx="50" cy="50" r="30" className={styles.circle2} />
          <circle cx="50" cy="50" r="20" className={styles.circle3} />
        </svg>
      </div>
      <p className={styles.message}>{message}</p>
      <div className={styles.dots}>
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  );

  if (fullScreen) {
    return <div className={styles.fullScreen}>{content}</div>;
  }

  return <div className={styles.container}>{content}</div>;
}

AILoadingState.propTypes = {
  message: PropTypes.string,
  fullScreen: PropTypes.bool,
};

AILoadingState.defaultProps = {
  message: 'AI is thinking...',
  fullScreen: false,
};

export default AILoadingState;