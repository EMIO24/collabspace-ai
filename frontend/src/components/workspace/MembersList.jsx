import React, { useState } from 'react';
import PropTypes from 'prop-types';
import styles from './MembersList.module.css';
import InviteMembersModal from '../../pages/Workspaces/InviteMembersModal';

export default function MembersList({ members, workspaceId }) {
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h3>Current Members ({members.length})</h3>
        {workspaceId && (
            <button className={styles.inviteBtn} onClick={() => setIsInviteModalOpen(true)}>
                Invite New Member
            </button>
        )}
      </header>

      <ul className={styles.list}>
        {members.length === 0 ? (
          <li className={styles.empty}>No members in this workspace yet.</li>
        ) : (
          members.map((member) => (
            <li key={member.id} className={styles.memberItem}>
              <img className={styles.avatar} src={member.avatar || '/avatar-placeholder.png'} alt={member.name} />
              <div className={styles.info}>
                <div className={styles.name}>{member.name}</div>
                <div className={styles.role}>{member.role || 'Member'}</div>
              </div>
            </li>
          ))
        )}
      </ul>

      {workspaceId && (
        <InviteMembersModal
          isOpen={isInviteModalOpen}
          onClose={() => setIsInviteModalOpen(false)}
          workspaceId={workspaceId}
        />
      )}
    </div>
  );
}

MembersList.propTypes = {
  members: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    avatar: PropTypes.string,
    role: PropTypes.string,
  })).isRequired,
  workspaceId: PropTypes.string,
};