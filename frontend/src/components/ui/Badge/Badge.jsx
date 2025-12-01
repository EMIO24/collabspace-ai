import React from 'react';
import clsx from 'clsx';
import styles from './Badge.module.css';

const Badge = ({ variant = 'gray', children, className }) => {
  return (
    <span className={clsx(styles.badge, styles[variant], className)}>
      {children}
    </span>
  );
};

export default Badge;