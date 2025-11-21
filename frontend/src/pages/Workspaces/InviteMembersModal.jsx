import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useForm } from 'react-hook-form';
import styles from './InviteMembersModal.module.css';
import { inviteWorkspaceMembers } from '@api/workspaces'; // Assume this API exists
import { pushNotification } from '@store/slices/notificationSlice';
import { useDispatch } from 'react-redux';

export default function InviteMembersModal({ isOpen, onClose, workspaceId }) {
  const dispatch = useDispatch();
  const { handleSubmit, formState: { isSubmitting }, reset } = useForm();
  const [emails, setEmails] = useState([]);
  const [emailInput, setEmailInput] = useState('');

  if (!isOpen) return null;

  const emailPattern = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;

  const handleAddEmail = (e) => {
    e.preventDefault();
    const newEmail = emailInput.trim();

    if (!newEmail) return;

    if (!emailPattern.test(newEmail)) {
      dispatch(pushNotification({ id: Date.now(), message: 'Invalid email format.', type: 'error' }));
    } else if (emails.includes(newEmail)) {
      dispatch(pushNotification({ id: Date.now(), message: 'Email is already added.', type: 'warning' }));
    } else {
      setEmails([...emails, newEmail]);
      setEmailInput('');
    }
  };

  const handleRemoveEmail = (emailToRemove) => {
    setEmails(emails.filter(email => email !== emailToRemove));
  };

  const onSubmit = async () => {
    if (emails.length === 0) {
      dispatch(pushNotification({ id: Date.now(), message: 'Please add at least one email address.', type: 'warning' }));
      return;
    }

    try {
      await inviteWorkspaceMembers(workspaceId, emails);
      dispatch(pushNotification({ id: Date.now(), message: `Sent ${emails.length} invitation(s).` }));
      onClose();
      reset();
      setEmails([]);
    } catch (error) {
      console.error('Invitation failed:', error);
      dispatch(pushNotification({ id: Date.now(), message: `Invitation failed: ${error.message || 'Unknown error'}`, type: 'error' }));
    }
  };

  return (
    <div className={styles.modalBackdrop}>
      <div className={styles.modalContent}>
        <header className={styles.header}>
          <h2>Invite Members</h2>
          <button className={styles.closeBtn} onClick={onClose}>&times;</button>
        </header>

        <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="emailInput">Email Addresses to Invite</label>
            <div className={styles.emailInputGroup}>
              <input
                id="emailInput"
                type="email"
                placeholder="Enter email"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleAddEmail(e); }}
                disabled={isSubmitting}
              />
              <button type="button" className={styles.addEmailBtn} onClick={handleAddEmail} disabled={isSubmitting}>Add</button>
            </div>
          </div>

          <div className={styles.tagContainer}>
            {emails.map((email) => (
              <span key={email} className={styles.emailTag}>
                {email}
                <button type="button" onClick={() => handleRemoveEmail(email)}>&times;</button>
              </span>
            ))}
            {emails.length === 0 && <p className={styles.noEmails}>No emails added yet.</p>}
          </div>

          <footer className={styles.footer}>
            <button type="button" className={styles.cancelBtn} onClick={onClose} disabled={isSubmitting}>Cancel</button>
            <button type="submit" className={styles.submitBtn} disabled={isSubmitting || emails.length === 0}>
              {isSubmitting ? 'Sending...' : `Send ${emails.length} Invitation(s)`}
            </button>
          </footer>
        </form>
      </div>
    </div>
  );
}

InviteMembersModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  workspaceId: PropTypes.string.isRequired,
};