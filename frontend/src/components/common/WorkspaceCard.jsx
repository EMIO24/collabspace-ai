import React from 'react';
import PropTypes from 'prop-types';
import styles from './WorkspaceCard.module.css';
import { useNavigate } from 'react-router-dom';

export default function WorkspaceCard({ workspace, isSelected, onSelect }) {
  const navigate = useNavigate();

  const handleDetailsClick = (e) => {
    e.stopPropagation();
    navigate(`/workspaces/${workspace.id}`);
  };

  return (
    <div
      className={`${styles.card} ${isSelected ? styles.selected : ''}`}
      onClick={() => onSelect(workspace)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelect(workspace); }}
    >
      <div className={styles.icon}>{workspace.name.slice(0, 1)}</div>
      <h3 className={styles.title}>{workspace.name}</h3>
      <p className={styles.description}>{workspace.description || 'Collaborative space for the team.'}</p>
      <div className={styles.meta}>
        <span>{workspace.memberCount || '0'} Members</span>
      </div>
      <button className={styles.detailsBtn} onClick={handleDetailsClick}>View Details</button>
      {isSelected && <span className={styles.currentTag}>Current</span>}
    </div>
  );
}

WorkspaceCard.propTypes = {
  workspace: PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    description: PropTypes.string,
    memberCount: PropTypes.number,
  }).isRequired,
  isSelected: PropTypes.bool,
  onSelect: PropTypes.func.isRequired,
};