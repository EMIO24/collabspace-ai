import React, { useState } from 'react';
import clsx from 'clsx';
import styles from './Avatar.module.css';

const Avatar = ({ src, alt, fallback, size = 'md', className }) => {
  const [hasError, setHasError] = useState(false);

  return (
    <div className={clsx(styles.container, styles[size], className)}>
      {src && !hasError ? (
        <img 
          src={src} 
          alt={alt || 'Avatar'} 
          className={styles.image} 
          onError={() => setHasError(true)}
        />
      ) : (
        <div className={styles.fallback}>
          {fallback || (alt ? alt.charAt(0) : '?')}
        </div>
      )}
    </div>
  );
};

export default Avatar;