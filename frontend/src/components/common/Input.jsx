import React from 'react';
import PropTypes from 'prop-types';
import styles from './Input.module.css';

export default function Input({ label, error, id, ...props }) {
  return (
    <div className={styles.field}>
      {label && <label htmlFor={id} className={styles.label}>{label}</label>}
      <input id={id} className={`${styles.input} ${error ? styles.invalid : ''}`} {...props} />
      {error && <div className={styles.error}>{error}</div>}
    </div>
  );
}

Input.propTypes = {
  label: PropTypes.node,
  error: PropTypes.oneOfType([PropTypes.string, PropTypes.bool]),
  id: PropTypes.string,
};
