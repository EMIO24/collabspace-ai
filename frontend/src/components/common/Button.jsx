import React from 'react';
import PropTypes from 'prop-types';
import styles from './Button.module.css';

export default function Button({ children, variant = 'default', fullWidth, loading, ...props }) {
  const cls = `${styles.button} ${styles[variant]} ${fullWidth ? styles.full : ''}`;
  return (
    <button className={cls} disabled={loading || props.disabled} {...props}>
      {loading ? <span className={styles.loader} /> : children}
    </button>
  );
}

Button.propTypes = {
  children: PropTypes.node,
  variant: PropTypes.oneOf(['default', 'primary', 'danger']),
  fullWidth: PropTypes.bool,
  loading: PropTypes.bool,
};
