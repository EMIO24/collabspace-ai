import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Download, FileText, Image as ImageIcon, Film, ShieldAlert } from 'lucide-react';
import { api } from '../../services/api';
import styles from './SharedFileView.module.css';

const SharedFileView = () => {
  const { token } = useParams();

  const { data: file, isLoading, isError } = useQuery({
    queryKey: ['sharedFile', token],
    queryFn: async () => {
      const res = await api.get(`/files/shared/${token}/`);
      return res.data;
    },
    retry: false
  });

  const handleDownload = () => {
    if (file?.url) {
      window.open(file.url, '_blank');
    }
  };

  const getIcon = () => {
    if (!file) return <FileText size={48} className="text-gray-400" />;
    if (file.mime_type?.startsWith('image/')) return <ImageIcon size={48} className="text-purple-500" />;
    if (file.mime_type?.startsWith('video/')) return <Film size={48} className="text-pink-500" />;
    return <FileText size={48} className="text-blue-500" />;
  };

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className="animate-pulse flex flex-col items-center">
          <div className="w-24 h-24 bg-white/50 rounded-full mb-4"></div>
          <div className="h-6 w-48 bg-white/50 rounded"></div>
        </div>
      </div>
    );
  }

  if (isError || !file) {
    return (
      <div className={styles.container}>
        <div className={styles.card}>
          <div className={styles.previewCircle} style={{ background: '#fee2e2', borderColor: '#fecaca' }}>
            <ShieldAlert size={48} className="text-red-500" />
          </div>
          <h1 className={styles.fileName}>Link Expired</h1>
          <p className={styles.fileMeta}>
            This shared link is invalid or has expired. Please ask the owner to reshare it.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.previewCircle}>
          {file.mime_type?.startsWith('image/') ? (
            <img src={file.url} alt="Preview" className={styles.previewImg} />
          ) : (
            getIcon()
          )}
        </div>

        <h1 className={styles.fileName}>{file.name}</h1>
        <p className={styles.fileMeta}>
          {(file.size / 1024 / 1024).toFixed(2)} MB • Uploaded {new Date(file.uploaded_at).toLocaleDateString()}
        </p>

        <button className={styles.downloadBtn} onClick={handleDownload}>
          <Download size={20} /> Download File
        </button>

        <div className={styles.footer}>
          Shared via <span className={styles.logo}>CollabSpace AI</span>
        </div>
      </div>
    </div>
  );
};

export default SharedFileView;