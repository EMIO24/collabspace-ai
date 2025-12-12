import React, { useState } from 'react';
import { X, Users, BrainCircuit } from 'lucide-react';
import Avatar from '../../components/ui/Avatar/Avatar';
import Button from '../../components/ui/Button/Button';
import styles from './AssigneeSkillsModal.module.css';

const AssigneeSkillsModal = ({ members, onClose, onConfirm, isLoading }) => {
  // Initialize state with empty skills or pre-fill if available
  const [skills, setSkills] = useState(
    members.reduce((acc, member) => ({ ...acc, [member.id]: '' }), {})
  );

  const handleSkillChange = (id, value) => {
    setSkills(prev => ({ ...prev, [id]: value }));
  };

  const handleSubmit = () => {
    // Merge skills into the member objects for the AI context
    // We append the skills to the username so the AI sees "John (React, Node)"
    const enrichedMembers = members.map(m => ({
        id: m.id,
        email: m.email,
        username: skills[m.id] 
            ? `${m.username} (Skills: ${skills[m.id]})` 
            : `${m.username} (Generalist)` 
    }));
    
    onConfirm(enrichedMembers);
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <h3 className={styles.title}>
            <Users size={20} className="text-blue-500" /> 
            Team Context
          </h3>
          <button className={styles.closeBtn} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className={styles.content}>
          <p className={styles.description}>
            Add skills or roles for each member so the AI can pick the best person for this task.
          </p>
          
          <div className={styles.memberList}>
            {members.map(member => (
              <div key={member.id} className={styles.memberItem}>
                <Avatar src={member.avatar} fallback={member.username?.[0]} />
                <div className={styles.memberInfo}>
                  <div className={styles.memberName}>{member.username}</div>
                  <div className={styles.memberEmail}>{member.email}</div>
                </div>
                <div className={styles.skillInputWrapper}>
                   <input 
                      className={styles.skillInput}
                      placeholder="e.g. Frontend, Python, Design..."
                      value={skills[member.id] || ''}
                      onChange={(e) => handleSkillChange(member.id, e.target.value)}
                      autoFocus={members.indexOf(member) === 0}
                   />
                </div>
              </div>
            ))}
            {members.length === 0 && (
                <div className="text-center text-gray-400 py-4">No members found in this workspace.</div>
            )}
          </div>
        </div>

        <div className={styles.footer}>
           <Button variant="ghost" onClick={onClose}>Cancel</Button>
           <Button onClick={handleSubmit} isLoading={isLoading}>
              <BrainCircuit size={16} className="mr-2" /> Suggest Assignee
           </Button>
        </div>
      </div>
    </div>
  );
};

export default AssigneeSkillsModal;