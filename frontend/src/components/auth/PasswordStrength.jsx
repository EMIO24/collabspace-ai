import React from 'react';
import PropTypes from 'prop-types';
import styles from './PasswordStrength.module.css';
import { validatePasswordStrength } from '@utils/validators';

export default function PasswordStrength({ value }) {
  const { score, message } = validatePasswordStrength(value || '');
  const pct = Math.min((score / 5) * 100, 100);

  return (
    <div className={styles.wrap}>
      <div className={styles.bar}>
        <div className={styles.fill} style={{ width: `${pct}%` }} />
      </div>
      <div className={styles.label}>{message}</div>
    </div>
  );
}

PasswordStrength.propTypes = {
  value: PropTypes.string,
};
