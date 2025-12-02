import React, { useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  UploadCloud, File as FileIcon, FileText, Image as ImageIcon, 
  MoreVertical, Trash2, Download, Film 
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Button from '../../components/ui/Button/Button';
import styles from './ProjectFiles.module.css';

const ProjectFiles = () => {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  // --- DATA FETCHING ---
  // UPDATED: Using query param instead of nested route
  const { data: files, isLoading } = useQuery({
    queryKey: ['projectFiles', id],
    queryFn: async () => {
      const res = await api.get(`/files/?project=${id}`);
      return res.data;
    },
    enabled: !!id
  });

  // --- MUTATIONS ---
  // UPDATED: POST to /files/ directly
  const uploadMutation = useMutation({
    mutationFn: (formData) => api.post(`/files/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['projectFiles', id]);
      toast.success('File uploaded successfully');
    },
    onError: () => toast.error('Upload failed')
  });

  // UPDATED: DELETE to /files/{id}/ directly
  const deleteMutation = useMutation({
    mutationFn: (fileId) => api.delete(`/files/${fileId}/`),
    onSuccess: () => {
      queryClient.invalidateQueries(['projectFiles', id]);
      toast.success('File deleted');
    },
    onError: () => toast.error('Failed to delete file')
  });

  // --- HANDLERS ---
  const handleFileSelect = (e) => {
    if (e.target.files?.[0]) handleUpload(e.target.files[0]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.[0]) handleUpload(e.dataTransfer.files[0]);
  };

  const handleUpload = (file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', file.name);
    // UPDATED: Explicitly adding project ID to body
    formData.append('project', id);
    
    uploadMutation.mutate(formData);
  };

  const getFileIcon = (mimeType) => {
    // Safety check for mimeType
    const type = mimeType || '';
    if (type.startsWith('image/')) return <ImageIcon size={32} className="text-purple-500" />;
    if (type.startsWith('video/')) return <Film size={32} className="text-pink-500" />;
    if (type.includes('pdf')) return <FileText size={32} className="text-red-500" />;
    return <FileIcon size={32} className={styles.fileIcon} />;
  };

  const isImage = (mimeType) => (mimeType || '').startsWith('image/');

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading files...</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Project Files</h2>
        <Button onClick={() => fileInputRef.current?.click()}>
          Upload File
        </Button>
      </div>

      {/* Drop Zone */}
      <div 
        className={`${styles.dropzone} ${isDragging ? styles.dropzoneActive : ''}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className={styles.uploadIcon}>
          <UploadCloud size={32} />
        </div>
        <div>
          <div className={styles.dropText}>Click or drag files to upload</div>
          <div className={styles.dropSubtext}>Support for images, PDF, and archives (max 10MB)</div>
        </div>
        <input 
          type="file" 
          hidden 
          ref={fileInputRef} 
          onChange={handleFileSelect} 
        />
      </div>

      {/* Files Grid */}
      <div className={styles.grid}>
        {files?.map((file) => (
          <div key={file.id} className={styles.fileCard}>
            <div className={styles.actions}>
              <button 
                className={styles.actionBtn}
                onClick={(e) => {
                  e.stopPropagation();
                  if(confirm('Delete file?')) deleteMutation.mutate(file.id);
                }}
              >
                <Trash2 size={14} />
              </button>
            </div>

            <div className={styles.preview}>
              {isImage(file.mime_type) ? (
                <img src={file.url} alt={file.name} className={styles.previewImg} />
              ) : (
                getFileIcon(file.mime_type)
              )}
            </div>

            <div className={styles.fileName} title={file.name}>
              {file.name}
            </div>
            
            <div className={styles.fileMeta}>
              <span>{file.size ? (file.size / 1024 / 1024).toFixed(2) : '0'} MB</span>
              <span>•</span>
              <span>{file.uploaded_at ? new Date(file.uploaded_at).toLocaleDateString() : 'Unknown'}</span>
            </div>
          </div>
        ))}

        {!files?.length && (
          <div style={{ gridColumn: '1 / -1', textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
            No files uploaded yet.
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectFiles;