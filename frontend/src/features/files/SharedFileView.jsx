import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Download, FileText, Image as ImageIcon, Film, ShieldAlert, Clock, Lock, ArrowRight } from 'lucide-react';
import { api } from '../../services/api';
import Button from '../../components/ui/Button/Button';
import styles from './SharedFileView.module.css';
import { toast } from 'react-hot-toast';

const SharedFileView = () => {
  const { token } = useParams();
  const [password, setPassword] = useState('');
  const [isPasswordRequired, setIsPasswordRequired] = useState(false);

  // 1. Fetch File Data
  const { data: file, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['sharedFile', token],
    queryFn: async () => {
      try {
        // Pass password header if entered
        const headers = password ? { 'X-Share-Password': password } : {};
        const res = await api.get(`/files/shared/${token}/`, { headers });
        return res.data;
      } catch (err) {
        if (err.response?.status === 403 && err.response?.data?.code === 'password_required') {
           setIsPasswordRequired(true);
           return null; // Halt, show password UI
        }
        throw err;
      }
    },
    retry: false
  });

  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    refetch(); // Retry query with password state
  };

  const handleDownload = () => {
    if (file?.url) {
      window.open(file.url, '_blank');
      toast.success('Download started');
    }
  };

  const getIcon = (mimeType) => {
    if (mimeType?.startsWith('image/')) return <ImageIcon size={64} className="text-purple-500" />;
    if (mimeType?.startsWith('video/')) return <Film size={64} className="text-pink-500" />;
    return <FileText size={64} className="text-blue-500" />;
  };

  const formatSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  // --- RENDER STATES ---

  // 1. Loading
  if (isLoading && !isPasswordRequired) {
    return (
      <div className={styles.container}>
        <div className={styles.card}>
           <div className="w-24 h-24 bg-gray-100 rounded-full animate-pulse mb-6" />
           <div className="h-8 w-48 bg-gray-100 rounded animate-pulse mb-2" />
           <div className="h-4 w-32 bg-gray-100 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  // 2. Error / Expired
  if (isError && !isPasswordRequired) {
    return (
      <div className={styles.container}>
        <div className={styles.card}>
          <div className={styles.previewCircle} style={{ borderColor: '#fee2e2', background: '#fef2f2' }}>
            <ShieldAlert size={48} className="text-red-500" />
          </div>
          <h1 className={styles.fileName}>Link Unavailable</h1>
          <p className={styles.fileMeta}>
             This link may have expired, been deleted, or does not exist.
          </p>
          <div className={styles.footer}>
             CollabSpace AI • Secure Sharing
          </div>
        </div>
      </div>
    );
  }

  // 3. Password Required
  if (isPasswordRequired && !file) {
      return (
        <div className={styles.container}>
            <div className={styles.card}>
                <div className={styles.brand}>
                    <div className={styles.brandLogo}>C</div>
                    CollabSpace
                </div>
                <div className={styles.previewCircle} style={{ borderColor: '#e0e7ff', background: '#eef2ff' }}>
                    <Lock size={48} className="text-indigo-500" />
                </div>
                <h1 className={styles.fileName} style={{ fontSize: '1.25rem' }}>Password Protected</h1>
                <p className={styles.fileMeta}>Please enter the password to view this file.</p>
                
                <form onSubmit={handlePasswordSubmit} className={styles.passwordForm}>
                    <input 
                        type="password" 
                        className={styles.passwordInput}
                        placeholder="••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoFocus
                    />
                    <button type="submit" className={styles.downloadBtn}>
                       Access File <ArrowRight size={20} />
                    </button>
                </form>
            </div>
        </div>
      );
  }

  // 4. File View
  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.brand}>
            <div className={styles.brandLogo}>C</div>
            CollabSpace
        </div>

        <div className={styles.previewCircle}>
          {file.mime_type?.startsWith('image/') ? (
            <img src={file.url} alt="Preview" className={styles.previewImg} />
          ) : (
            getIcon(file.mime_type)
          )}
        </div>

        <h1 className={styles.fileName} title={file.name}>{file.name}</h1>
        
        <p className={styles.fileMeta}>
          {formatSize(file.size)} • Shared by {file.uploaded_by?.full_name || 'User'} on {new Date(file.created_at).toLocaleDateString()}
        </p>

        {file.expires_at && (
            <div className={styles.expiration}>
                <Clock size={14} /> Link expires on {new Date(file.expires_at).toLocaleDateString()}
            </div>
        )}

        <button className={styles.downloadBtn} onClick={handleDownload}>
          <Download size={20} /> Download File
        </button>

        <div className={styles.footer}>
          Shared securely via <strong>CollabSpace AI</strong>
        </div>
      </div>
    </div>
  );
};

export default SharedFileView;