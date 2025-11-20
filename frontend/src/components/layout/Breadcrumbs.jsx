import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import styles from './Breadcrumbs.module.css';

export default function Breadcrumbs() {
  const { pathname } = useLocation();
  const parts = pathname.split('/').filter(Boolean);
  const crumbs = parts.map((part, idx) => {
    const url = '/' + parts.slice(0, idx + 1).join('/');
    // pretty label
    const label = part.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    const isLast = idx === parts.length - 1;
    return { url, label, isLast };
  });

  if (crumbs.length === 0) return null;

  return (
    <nav className={styles.wrap} aria-label="Breadcrumbs">
      <ol className={styles.list}>
        <li><Link to="/dashboard">Home</Link></li>
        {crumbs.map((c) => (
          <li key={c.url} className={c.isLast ? styles.active : undefined}>
            {c.isLast ? <span>{c.label}</span> : <Link to={c.url}>{c.label}</Link>}
          </li>
        ))}
      </ol>
    </nav>
  );
}
