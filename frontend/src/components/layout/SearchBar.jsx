import React, { useState } from 'react';
import styles from './SearchBar.module.css';
import { useNavigate } from 'react-router-dom';

export default function SearchBar() {
  const [q, setQ] = useState('');
  const nav = useNavigate();

  const onSubmit = (e) => {
    e.preventDefault();
    const query = q.trim();
    if (!query) return;
    nav(`/search?q=${encodeURIComponent(query)}`);
    setQ('');
  };

  return (
    <form onSubmit={onSubmit} className={styles.form} role="search" aria-label="Search">
      <input
        className={styles.input}
        placeholder="Search projects, tasks, people..."
        value={q}
        onChange={(e) => setQ(e.target.value)}
        aria-label="Search"
      />
      <button className={styles.btn} type="submit" aria-label="Search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M21 21l-4.35-4.35"/><circle cx="11" cy="11" r="6" /></svg>
      </button>
    </form>
  );
}
