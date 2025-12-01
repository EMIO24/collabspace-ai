import React, { useState, useRef, useEffect } from 'react';
import { ChevronsUpDown, Plus, Check } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';
import CreateWorkspaceModal from './CreateWorkspaceModal';
import styles from './WorkspaceSwitcher.module.css';

const WorkspaceSwitcher = () => {
  const { workspaces, currentWorkspace, setCurrentWorkspace } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (ws) => {
    setCurrentWorkspace(ws);
    setIsOpen(false);
  };

  // If no workspace is loaded yet, render placeholder or null
  if (!currentWorkspace) return null;

  return (
    <div className={styles.container} ref={dropdownRef}>
      <button className={styles.trigger} onClick={() => setIsOpen(!isOpen)}>
        <div className={styles.avatar}>
          {currentWorkspace.name.charAt(0).toUpperCase()}
        </div>
        <div className={styles.info}>
          <span className={styles.name}>{currentWorkspace.name}</span>
          <span className={styles.role}>Owner</span>
        </div>
        <ChevronsUpDown size={16} className={styles.icon} />
      </button>

      {isOpen && (
        <div className={styles.dropdown}>
          {workspaces.map((ws) => (
            <button
              key={ws.id}
              className={`${styles.menuItem} ${ws.id === currentWorkspace.id ? styles.menuItemActive : ''}`}
              onClick={() => handleSelect(ws)}
            >
              <div className={`${styles.avatar} ${styles.avatarSmall}`}>
                {ws.name.charAt(0).toUpperCase()}
              </div>
              <span className={styles.itemName}>{ws.name}</span>
              {ws.id === currentWorkspace.id && <Check size={14} />}
            </button>
          ))}
          
          <div className={styles.separator} />
          
          <button 
            className={`${styles.menuItem} ${styles.createButton}`}
            onClick={() => {
              setIsOpen(false);
              setShowModal(true);
            }}
          >
            <Plus size={16} />
            Create Workspace
          </button>
        </div>
      )}

      {showModal && <CreateWorkspaceModal onClose={() => setShowModal(false)} />}
    </div>
  );
};

export default WorkspaceSwitcher;