import React, { useState } from 'react';
import { createProject } from '../../api/projects';
import styles from './CreateProjectModal.module.css';

function CreateProjectModal({ onClose, onProjectCreated }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    status: 'planning',
    priority: 'medium',
    startDate: '',
    endDate: '',
    budget: '',
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required';
    }

    if (formData.startDate && formData.endDate) {
      if (new Date(formData.endDate) < new Date(formData.startDate)) {
        newErrors.endDate = 'End date must be after start date';
      }
    }

    if (formData.budget && isNaN(formData.budget)) {
      newErrors.budget = 'Budget must be a number';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) return;

    try {
      setIsSubmitting(true);
      const projectData = {
        ...formData,
        budget: formData.budget ? parseFloat(formData.budget) : null,
      };
      const response = await createProject(projectData);
      onProjectCreated(response.data);
    } catch (error) {
      console.error('Failed to create project:', error);
      setErrors({ submit: 'Failed to create project. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2 className={styles.title}>Create New Project</h2>
          <button className={styles.closeButton} onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <label className={styles.label}>
              Project Name <span className={styles.required}>*</span>
            </label>
            <input
              type="text"
              name="name"
              className={`${styles.input} ${errors.name ? styles.error : ''}`}
              value={formData.name}
              onChange={handleChange}
              placeholder="Enter project name"
            />
            {errors.name && <span className={styles.errorText}>{errors.name}</span>}
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>Description</label>
            <textarea
              name="description"
              className={styles.textarea}
              value={formData.description}
              onChange={handleChange}
              placeholder="Enter project description"
              rows="4"
            />
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Status</label>
              <select
                name="status"
                className={styles.select}
                value={formData.status}
                onChange={handleChange}
              >
                <option value="planning">Planning</option>
                <option value="active">Active</option>
                <option value="on_hold">On Hold</option>
                <option value="completed">Completed</option>
              </select>
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Priority</label>
              <select
                name="priority"
                className={styles.select}
                value={formData.priority}
                onChange={handleChange}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Start Date</label>
              <input
                type="date"
                name="startDate"
                className={styles.input}
                value={formData.startDate}
                onChange={handleChange}
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>End Date</label>
              <input
                type="date"
                name="endDate"
                className={`${styles.input} ${errors.endDate ? styles.error : ''}`}
                value={formData.endDate}
                onChange={handleChange}
              />
              {errors.endDate && <span className={styles.errorText}>{errors.endDate}</span>}
            </div>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>Budget ($)</label>
            <input
              type="number"
              name="budget"
              className={`${styles.input} ${errors.budget ? styles.error : ''}`}
              value={formData.budget}
              onChange={handleChange}
              placeholder="Enter budget amount"
              min="0"
              step="0.01"
            />
            {errors.budget && <span className={styles.errorText}>{errors.budget}</span>}
          </div>

          {errors.submit && (
            <div className={styles.submitError}>{errors.submit}</div>
          )}

          <div className={styles.actions}>
            <button
              type="button"
              className={styles.cancelButton}
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={styles.submitButton}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating...' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CreateProjectModal;