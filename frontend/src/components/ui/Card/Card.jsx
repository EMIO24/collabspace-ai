import React from 'react';
import clsx from 'clsx';
import styles from './Card.module.css';

const Card = ({ children, className, ...props }) => {
  return (
    <div className={clsx(styles.card, className)} {...props}>
      {children}
    </div>
  );
};

export default Card;