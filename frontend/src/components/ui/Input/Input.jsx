import React from 'react';
import clsx from 'clsx';
import styles from './Input.module.css';

const Input = React.forwardRef(({ 
  label, 
  icon: Icon, 
  error, 
  className, 
  ...props 
}, ref) => {
  return (
    <div className={clsx(styles.wrapper, className)}>
      {label && <label className={styles.label}>{label}</label>}
      <div className={styles.inputContainer}>
        {Icon && <Icon size={18} className={styles.icon} />}
        <input
          ref={ref}
          className={clsx(styles.input, error && styles.error)}
          style={{ paddingLeft: Icon ? '2.75rem' : '1rem' }}
          {...props}
        />
      </div>
      {error && <span className={styles.errorMessage}>{error}</span>}
    </div>
  );
});

export default Input;