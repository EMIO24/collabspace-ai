import React from 'react';
import PropTypes from 'prop-types';
import styles from './Widget.module.css';

/**
 * A reusable container for dashboard widgets.
 * @param {object} props
 * @param {string} props.title - The title of the widget.
 * @param {React.ReactNode} [props.action] - Optional element (like a Link or Button) for the header.
 * @param {React.ReactNode} props.children - The main content of the widget.
 * @param {string} [props.className] - Optional additional class for the container.
 */
export default function Widget({ title, action, children, className = '' }) {
  return (
    <div className={`${styles.widget} ${className}`}>
      <header className={styles.header}>
        <h3 className={styles.title}>{title}</h3>
        {action && <div className={styles.action}>{action}</div>}
      </header>
      <div className={styles.content}>
        {children}
      </div>
    </div>
  );
}

Widget.propTypes = {
  title: PropTypes.string.isRequired,
  action: PropTypes.node,
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
};