import React from 'react';
import styles from './Button.module.css';

const Button = ({ 
  children, 
  variant = 'primary', // primary, danger, ghost
  isLoading = false, 
  className = '', 
  disabled,
  ...props 
}) => {
  const variantClass = styles[variant] || styles.primary;
  
  return (
    <button 
      className={`${styles.button} ${variantClass} ${className}`} 
      disabled={isLoading || disabled}
      {...props}
    >
      {isLoading && <span className={styles.spinner}></span>}
      {children}
    </button>
  );
};

export default Button;