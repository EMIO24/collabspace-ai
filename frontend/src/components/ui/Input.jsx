import React from 'react';
import styles from './Input.module.css';

const Input = ({ label, className = '', id, ...props }) => {
  return (
    <div className={styles.container}>
      {label && <label htmlFor={id} className={styles.label}>{label}</label>}
      <input 
        id={id} 
        className={`${styles.input} ${className}`} 
        {...props} 
      />
    </div>
  );
};

export default Input;