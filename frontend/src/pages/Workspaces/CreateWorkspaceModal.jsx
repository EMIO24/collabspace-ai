import React from 'react';
import PropTypes from 'prop-types';
import { useForm } from 'react-hook-form';
import styles from './CreateWorkspaceModal.module.css';
import { useDispatch } from 'react-redux';
import { createWorkspace } from '@api/workspaces'; // Assume this API exists
import { fetchWorkspaces } from '@store/slices/workspaceSlice';

export default function CreateWorkspaceModal({ isOpen, onClose }) {
  const dispatch = useDispatch();
  const { register, handleSubmit, formState: { errors, isSubmitting }, reset } = useForm();

  if (!isOpen) return null;

  const onSubmit = async (data) => {
    try {
      await createWorkspace(data);
      dispatch(fetchWorkspaces()); // Refresh list
      onClose();
      reset();
      // dispatch(pushNotification...)
    } catch (error) {
      console.error('Workspace creation failed:', error);
      // Handle error notification
    }
  };

  return (
    <div className={styles.modalBackdrop}>
      <div className={styles.modalContent}>
        <header className={styles.header}>
          <h2>Create New Workspace</h2>
          <button className={styles.closeBtn} onClick={onClose}>&times;</button>
        </header>

        <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="name">Workspace Name</label>
            <input
              id="name"
              {...register('name', { required: 'Name is required', minLength: { value: 3, message: 'Minimum 3 characters' } })}
              placeholder="e.g., Marketing Team"
              className={errors.name ? styles.inputError : ''}
            />
            {errors.name && <p className={styles.error}>{errors.name.message}</p>}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="description">Description (Optional)</label>
            <textarea
              id="description"
              {...register('description')}
              rows="3"
              placeholder="A brief description of this workspace's purpose."
            />
          </div>

          <footer className={styles.footer}>
            <button type="button" className={styles.cancelBtn} onClick={onClose}>Cancel</button>
            <button type="submit" className={styles.submitBtn} disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create Workspace'}
            </button>
          </footer>
        </form>
      </div>
    </div>
  );
}

CreateWorkspaceModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};