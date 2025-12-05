import React from 'react';
import { Check, Eye, Edit3, Trash2, Archive, Calendar, Globe, Smartphone, Bot } from 'lucide-react';
import styles from './ProjectCard.module.css';

// Helper to pick icons based on project name (Visual Polish)
const getProjectIcon = (name) => {
  const lower = (name || '').toLowerCase();
  if (lower.includes('web')) return <Globe size={24} className="text-blue-500" />;
  if (lower.includes('app') || lower.includes('mobile')) return <Smartphone size={24} className="text-purple-500" />;
  if (lower.includes('ai') || lower.includes('bot')) return <Bot size={24} className="text-green-500" />;
  return <div style={{ fontSize: '1.5rem' }}>📁</div>;
};

// Helper for Progress Color
const getProgressColor = (value) => {
  if (value >= 100) return '#10b981'; // Green
  if (value > 50) return '#3b82f6';   // Blue
  return '#8b5cf6';                   // Purple
};

const ProjectCard = ({ 
  project, 
  onClick, 
  selectable = false, 
  selected = false, 
  onSelect,
  onEdit,
  onDelete,
  onArchive
}) => {
  
  const handleAction = (e, actionFn) => {
    e.stopPropagation();
    if (actionFn) actionFn(project);
  };

  const handleSelect = (e) => {
    e.stopPropagation();
    if (onSelect) onSelect();
  };

  const progress = project.progress || 0;
  const statusKey = (project.status || 'active').toLowerCase().replace(' ', '_');

  return (
    <div 
      className={`${styles.card} ${selected ? styles.selected : ''}`} 
      onClick={onClick}
    >
      {/* Header: Icon & Selection */}
      <div className={styles.header}>
        <div className={styles.iconBox}>
          {getProjectIcon(project.name)}
        </div>
        
        {selectable && (
          <div 
            className={`${styles.checkbox} ${selected ? styles.checkboxSelected : ''}`}
            onClick={handleSelect}
          >
            {selected && <Check size={14} />}
          </div>
        )}
      </div>

      {/* Content */}
      <div className={styles.content}>
        <h3 className={styles.title}>{project.name}</h3>
        <p className={styles.description}>
          {project.description || 'No description provided.'}
        </p>
      </div>

      {/* Progress Bar */}
      <div className={styles.progressSection}>
        <div className={styles.progressHeader}>
          <span>Progress</span>
          <span>{progress}%</span>
        </div>
        <div className={styles.barBg}>
          <div 
            className={styles.barFill} 
            style={{ 
              width: `${progress}%`,
              background: getProgressColor(progress)
            }} 
          />
        </div>
      </div>

      {/* Footer: Team & Status */}
      <div className={styles.footer}>
        <div className={styles.avatarStack}>
          {/* Use real members if available, else visual placeholder logic */}
          {project.members && project.members.length > 0 ? (
             project.members.slice(0, 3).map((m) => (
               <div key={m.id} className={styles.avatar} title={m.username}>
                 {m.avatar ? <img src={m.avatar} alt="u" className="w-full h-full object-cover rounded-full" /> : (m.username?.[0] || 'U').toUpperCase()}
               </div>
             ))
          ) : (
             // Fallback styling matching dashboard logic
             ['A', 'B', 'C'].map((initial, i) => (
                <div key={i} className={styles.avatar}>{initial}</div>
             ))
          )}
          {(project.members?.length || 3) > 3 && (
             <div className={styles.avatar} style={{ background: '#f1f5f9', color: '#64748b' }}>+{(project.members?.length || 3) - 3}</div>
          )}
        </div>

        <span className={`${styles.badge} ${styles[`badge_${statusKey}`] || styles.badge_active}`}>
          {project.status || 'Active'}
        </span>
      </div>

      {/* Hover Actions Overlay */}
      {/* Only show if not in "selection mode" or if desired */}
      {!selected && (
        <div className={styles.overlay}>
           <button 
             className={styles.actionBtn} 
             onClick={(e) => handleAction(e, onClick)} 
             title="View Details"
           >
             <Eye size={18} />
           </button>
           {onEdit && (
             <button 
               className={styles.actionBtn} 
               onClick={(e) => handleAction(e, onEdit)} 
               title="Edit Project"
             >
               <Edit3 size={18} />
             </button>
           )}
           {onArchive && (
             <button 
               className={styles.actionBtn} 
               onClick={(e) => handleAction(e, onArchive)} 
               title="Archive"
             >
               <Archive size={18} />
             </button>
           )}
           {onDelete && (
             <button 
               className={`${styles.actionBtn} ${styles.deleteBtn}`} 
               onClick={(e) => handleAction(e, onDelete)} 
               title="Delete"
             >
               <Trash2 size={18} />
             </button>
           )}
        </div>
      )}
    </div>
  );
};

export default ProjectCard;