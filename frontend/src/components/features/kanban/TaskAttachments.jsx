import React, { useState, useEffect } from 'react';
import { getAttachments, uploadAttachment, deleteAttachment } from '../../api/attachments';
import styles from './TaskAttachments.module.css';

function TaskAttachments({ taskId }) {
  const [attachments, setAttachments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => {
    loadAttachments();
  }, [taskId]);

  const loadAttachments = async () => {
    try {
      const response = await getAttachments(taskId);
      setAttachments(response.data);
    } catch (error) {
      console.error('Failed to load attachments:', error);
    }
  };

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files);
    await uploadFiles(files);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    await uploadFiles(files);
  };

  const uploadFiles = async (files) => {
    if (files.length === 0) return;

    try {
      setIsUploading(true);
      const uploadPromises = files.map(file => 
        uploadAttachment(taskId, file)
      );
      const responses = await Promise.all(uploadPromises);
      const newAttachments = responses.map(r => r.data);
      setAttachments([...attachments, ...newAttachments]);
    } catch (error) {
      console.error('Failed to upload files:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (attachmentId) => {
    if (window.confirm('Delete this attachment?')) {
      try {
        await deleteAttachment(attachmentId);
        setAttachments(attachments.filter(a => a.id !== attachmentId));
      } catch (error) {
        console.error('Failed to delete attachment:', error);
      }
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    const iconMap = {
      pdf: '📄',
      doc: '📝',
      docx: '📝',
      xls: '📊',
      xlsx: '📊',
      ppt: '📽',
      pptx: '📽',
      jpg: '🖼',
      jpeg: '🖼',
      png: '🖼',
      gif: '🖼',
      zip: '📦',
      rar: '📦',
    };
    return iconMap[ext] || '📎';
  };

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Attachments ({attachments.length})</h3>

      <div
        className={`${styles.dropzone} ${dragOver ? styles.dragOver : ''}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-input"
          className={styles.fileInput}
          onChange={handleFileSelect}
          multiple
          disabled={isUploading}
        />
        <label htmlFor="file-input" className={styles.dropzoneLabel}>
          <svg className={styles.uploadIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <div>
            <span className={styles.uploadText}>
              {isUploading ? 'Uploading...' : 'Click to upload or drag and drop'}
            </span>
            <span className={styles.uploadHint}>PDF, DOC, XLS, PNG, JPG up to 10MB</span>
          </div>
        </label>
      </div>

      {attachments.length > 0 && (
        <div className={styles.attachmentsList}>
          {attachments.map(attachment => (
            <div key={attachment.id} className={styles.attachment}>
              <div className={styles.attachmentIcon}>
                {getFileIcon(attachment.filename)}
              </div>
              <div className={styles.attachmentInfo}>
                <div className={styles.attachmentName}>{attachment.filename}</div>
                <div className={styles.attachmentMeta}>
                  {formatFileSize(attachment.size)} • {new Date(attachment.createdAt).toLocaleDateString()}
                </div>
              </div>
              <div className={styles.attachmentActions}>
                <a
                  href={attachment.url}
                  download
                  className={styles.actionButton}
                  title="Download"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                </a>
                <button
                  className={`${styles.actionButton} ${styles.deleteButton}`}
                  onClick={() => handleDelete(attachment.id)}
                  title="Delete"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TaskAttachments;