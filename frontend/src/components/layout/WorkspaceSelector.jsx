import React, { useState } from 'react';
import PropTypes from 'prop-types';
import styles from './WorkspaceSelector.module.css';
import { useSelector, useDispatch } from 'react-redux';
import { setCurrentWorkspace } from '@store/slices/workspaceSlice';

/**
 * Workspace selector - shows current workspace name and allows switching.
 * Accepts "collapsed" prop to render compact UI.
 */
export default function WorkspaceSelector({ collapsed }) {
  const dispatch = useDispatch();
  const workspaces = useSelector((s) => s.workspace.list || []);
  const current = useSelector((s) => s.workspace.current);
  const [open, setOpen] = useState(false);

  function onSelect(ws) {
    dispatch(setCurrentWorkspace(ws));
    setOpen(false);
  }

  return (
    <div className={styles.wrap}>
      <button className={styles.trigger} onClick={() => setOpen((v) => !v)} aria-haspopup="listbox">
        <div className={styles.mark}>{(current?.name || 'W').slice(0,1)}</div>
        {!collapsed && (
          <div className={styles.meta}>
            <div className={styles.title}>{current?.name || 'Select workspace'}</div>
            <div className={styles.subtitle}>{workspaces.length} workspaces</div>
          </div>
        )}
        <svg className={styles.chev} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M6 9l6 6 6-6"/></svg>
      </button>

      {open && (
        <ul className={styles.list} role="listbox" aria-label="Workspaces">
          {workspaces.map((ws) => (
            <li key={ws.id} className={styles.item} onClick={() => onSelect(ws)} role="option" tabIndex={0}>
              <div className={styles.markSmall}>{(ws.name || 'W').slice(0,1)}</div>
              <div className={styles.label}>{ws.name}</div>
            </li>
          ))}
          <li className={styles.itemAdd}><a href="/workspaces/new">Create workspace</a></li>
        </ul>
      )}
    </div>
  );
}

WorkspaceSelector.propTypes = {
  collapsed: PropTypes.bool,
};
