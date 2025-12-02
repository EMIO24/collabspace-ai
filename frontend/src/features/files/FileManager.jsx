import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Folder, FileText, Image as ImageIcon, Film, 
  MoreVertical, Download, Share2, Trash2, Home, ChevronRight 
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import styles from './FileManager.module.css';

const FILE_TYPES = {
  all: 'All Files',
  images: 'Images',
  documents: 'Documents',
  media: 'Media'
};

const FileManager = () => {
  const [activeCategory, setActiveCategory] = useState('all');
  const [currentPath, setCurrentPath] = useState([{ id: 'root', name: 'Home' }]);
  const queryClient = useQueryClient();

  // 1. Fetch Files
  const { data: files, isLoading } = useQuery({
    queryKey: ['files', activeCategory],
    queryFn: async () => {
      // In a real app, you'd pass category/folder_id as params
      const res = await api.get('/files/');
      return res.data;
    }
  });

  // 2. Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/files/${id}/`),
    onSuccess: () => {
      toast.success('Item deleted');
      queryClient.invalidateQueries(['files']);
    }
  });

  // Mock folder navigation handler
  const handleFolderClick = (folderName) => {
    setCurrentPath([...currentPath, { id: 'mock-id', name: folderName }]);
    // Trigger fetch for new folder ID here
  };

  const navigateUp = (index) => {
    setCurrentPath(currentPath.slice(0, index + 1));
  };

  const getFileIcon = (mimeType) => {
    if (!mimeType) return <Folder size={48} className={styles.iconFolder} />;
    if (mimeType.startsWith('image/')) return <ImageIcon size={32} className="text-purple-500" />;
    if (mimeType.startsWith('video/')) return <Film size={32} className="text-pink-500" />;
    return <FileText size={32} className="text-blue-500" />;
  };

  return (
    <div className={styles.container}>
      {/* Sidebar */}
      <div className={styles.sidebar}>
        <div className={styles.sidebarHeader}>My Drive</div>
        <nav>
          {Object.entries(FILE_TYPES).map(([key, label]) => (
            <div 
              key={key}
              className={`${styles.navItem} ${activeCategory === key ? styles.activeNav : ''}`}
              onClick={() => setActiveCategory(key)}
            >
              {key === 'all' ? <Folder size={18} /> : <FileText size={18} />}
              {label}
            </div>
          ))}
        </nav>

        <div className={styles.storageInfo}>
          <div className="flex justify-between text-xs font-semibold text-gray-600 mb-1">
            <span>Storage</span>
            <span>75%</span>
          </div>
          <div className={styles.storageBar}>
            <div className={styles.storageFill} style={{ width: '75%' }} />
          </div>
          <div className="text-xs text-gray-400 mt-2">7.5 GB of 10 GB used</div>
        </div>
      </div>

      {/* Main Area */}
      <div className={styles.main}>
        {/* Breadcrumbs */}
        <div className={styles.toolbar}>
          <div className={styles.breadcrumbs}>
            {currentPath.map((crumb, index) => (
              <React.Fragment key={crumb.id}>
                {index > 0 && <ChevronRight size={16} />}
                <span 
                  className={`${styles.crumb} ${index === currentPath.length - 1 ? styles.currentCrumb : ''}`}
                  onClick={() => navigateUp(index)}
                >
                  {index === 0 ? <Home size={16} /> : crumb.name}
                </span>
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Grid */}
        <div className={styles.grid}>
          {isLoading ? (
            <div>Loading files...</div>
          ) : (
            <>
              {/* Mock Folders */}
              <div className={styles.fileCard} onClick={() => handleFolderClick('Projects')}>
                <div className={styles.preview}>
                  <Folder size={48} className={styles.iconFolder} />
                </div>
                <div className={styles.fileName}>Projects</div>
                <div className={styles.fileMeta}>12 items</div>
              </div>

              {/* Files */}
              {files?.map((file) => (
                <div key={file.id} className={styles.fileCard}>
                  <button className={styles.contextBtn} onClick={(e) => {
                    e.stopPropagation();
                    // Open context menu logic here
                  }}>
                    <MoreVertical size={16} />
                  </button>

                  <div className={styles.preview}>
                    {file.mime_type?.startsWith('image/') ? (
                      <img src={file.url} alt={file.name} className={styles.previewImg} />
                    ) : getFileIcon(file.mime_type)}
                  </div>
                  
                  <div className={styles.fileName} title={file.name}>{file.name}</div>
                  <div className={styles.fileMeta}>
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileManager;