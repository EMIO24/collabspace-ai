import React, { useState, useMemo, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Folder, FileText, Image as ImageIcon, Film, MoreVertical, 
  Download, Share2, Trash2, Home, ChevronRight, UploadCloud, 
  Grid, List, Search, Star, Clock, X, Copy
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import Button from '../../components/ui/Button/Button';
import Avatar from '../../components/ui/Avatar/Avatar';
import styles from './FileManager.module.css';

const FILE_TYPES = {
  all: { label: 'All Files', icon: Folder },
  images: { label: 'Images', icon: ImageIcon },
  documents: { label: 'Documents', icon: FileText },
  media: { label: 'Media', icon: Film },
};

const FileManager = () => {
  const { currentWorkspace } = useWorkspace();
  const queryClient = useQueryClient();
  const fileInputRef = useRef(null);
  
  // State
  const [viewMode, setViewMode] = useState('grid');
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [previewFile, setPreviewFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [openMenuId, setOpenMenuId] = useState(null);

  useEffect(() => {
    const closeMenu = () => setOpenMenuId(null);
    if (openMenuId) document.addEventListener('click', closeMenu);
    return () => document.removeEventListener('click', closeMenu);
  }, [openMenuId]);

  // 1. Fetch Files (FIX: Added workspace param)
  const { data: rawData, isLoading } = useQuery({
    queryKey: ['files', currentWorkspace?.id],
    queryFn: async () => {
      if (!currentWorkspace?.id) return [];
      const res = await api.get(`/files/?workspace=${currentWorkspace.id}`);
      return res.data;
    },
    enabled: !!currentWorkspace?.id
  });

  // 2. Fetch Storage Stats (FIX: Added workspace param to prevent 400 Error)
  const { data: storage } = useQuery({
    queryKey: ['storage', currentWorkspace?.id],
    queryFn: async () => {
      if (!currentWorkspace?.id) return { used: 0, limit: 10737418240 };
      try {
          const res = await api.get(`/files/storage-stats/?workspace=${currentWorkspace.id}`);
          return res.data;
      } catch {
          return { used: 0, limit: 10737418240 };
      }
    },
    enabled: !!currentWorkspace?.id
  });

  // Normalize & Filter Data
  const files = useMemo(() => {
    let rawList = [];
    if (Array.isArray(rawData)) rawList = rawData;
    else if (rawData?.results) rawList = rawData.results;
    
    // FIX: Map API fields to component expectations
    let list = rawList.map(item => ({
      ...item,
      name: item.file_name || item.name,
      mime_type: item.file_type || item.mime_type,
      url: item.cloudinary_url || item.file || item.url,
      size: item.file_size || item.size,
      uploaded_at: item.created_at || item.uploaded_at
    }));
    
    if (searchQuery) {
        list = list.filter(f => f.name.toLowerCase().includes(searchQuery.toLowerCase()));
    }

    if (activeCategory === 'images') {
        list = list.filter(f => f.mime_type?.startsWith('image/'));
    } else if (activeCategory === 'media') {
        list = list.filter(f => f.mime_type?.startsWith('video/') || f.mime_type?.startsWith('audio/'));
    } else if (activeCategory === 'documents') {
        list = list.filter(f => f.mime_type?.includes('pdf') || f.mime_type?.includes('text') || f.mime_type?.includes('word'));
    }

    return list;
  }, [rawData, searchQuery, activeCategory]);

  // Mutations
  const uploadMutation = useMutation({
    mutationFn: (formData) => api.post('/files/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['files']);
      queryClient.invalidateQueries(['storage']);
      toast.success('File uploaded');
    },
    onError: (err) => {
        const msg = err.response?.data?.error || 'Upload failed';
        toast.error(msg);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/files/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries(['files']);
      queryClient.invalidateQueries(['storage']);
      toast.success('File deleted');
      setPreviewFile(null);
    }
  });

  const bulkDeleteMutation = useMutation({
    mutationFn: async (ids) => {
        await Promise.all(ids.map(id => api.delete(`/files/${id}/`)));
    },
    onSuccess: () => {
        queryClient.invalidateQueries(['files']);
        setSelectedIds(new Set());
        toast.success('Selected files deleted');
    }
  });

  const handleUpload = (files) => {
    if (!currentWorkspace) return toast.error("No workspace selected");
    
    Array.from(files).forEach(file => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', file.name);
        // Ensure workspace ID is sent with upload
        formData.append('workspace', currentWorkspace.id);
        uploadMutation.mutate(formData);
    });
  };

  const toggleSelection = (id) => {
    const newSet = new Set(selectedIds);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedIds(newSet);
  };

  const copyLink = (fileId) => {
    const link = `${window.location.origin}/shared/${fileId}`;
    navigator.clipboard.writeText(link);
    toast.success('Link copied to clipboard');
  };

  const getFileIcon = (mimeType) => {
    if (mimeType?.startsWith('image/')) return <ImageIcon size={32} className={styles.textPurple} />;
    if (mimeType?.startsWith('video/')) return <Film size={32} className={styles.textPink} />;
    if (mimeType?.includes('pdf')) return <FileText size={32} className={styles.textRed} />;
    return <FileText size={32} className={styles.textBlue} />;
  };

  const formatSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const usedStorage = storage?.used || files.reduce((acc, f) => acc + (f.size || 0), 0);
  const totalStorage = storage?.limit || 10737418240;
  const storagePercent = Math.min((usedStorage / totalStorage) * 100, 100);

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
         <div className={styles.breadcrumbs}>
            <span className={styles.crumb}><Home size={16}/> Home</span>
            <ChevronRight size={14} />
            <span className={styles.activeCrumb}>Files</span>
         </div>
         
         <div className={styles.headerControls}>
            <div className={styles.viewToggle}>
               <button className={`${styles.viewBtn} ${viewMode === 'grid' ? styles.activeView : ''}`} onClick={() => setViewMode('grid')}>
                  <Grid size={16} />
               </button>
               <button className={`${styles.viewBtn} ${viewMode === 'list' ? styles.activeView : ''}`} onClick={() => setViewMode('list')}>
                  <List size={16} />
               </button>
            </div>
            <Button onClick={() => fileInputRef.current?.click()}>
               <UploadCloud size={16} className={styles.iconMr} /> Upload
            </Button>
            <input 
               type="file" multiple hidden ref={fileInputRef} 
               onChange={(e) => handleUpload(e.target.files)} 
            />
         </div>
      </div>

      <div className={styles.layout}>
         {/* Sidebar */}
         <div className={styles.sidebar}>
            <div className={styles.storageWidget}>
               <div className={styles.storageHeader}>
                  <span>Storage</span>
                  <span>{storagePercent.toFixed(0)}%</span>
               </div>
               <div className={styles.storageBar}>
                  <div className={styles.storageFill} style={{ width: `${storagePercent}%` }} />
               </div>
               <div className={styles.storageDetails}>
                  <span>{formatSize(usedStorage)} used</span>
                  <span>{formatSize(totalStorage)}</span>
               </div>
               <button className={styles.upgradeBtn}>Upgrade Storage</button>
            </div>

            <div className={styles.filterSection}>
               <div className={styles.filterHeader}>Categories</div>
               {Object.entries(FILE_TYPES).map(([key, type]) => {
                  const Icon = type.icon;
                  return (
                     <div 
                        key={key} 
                        className={`${styles.filterItem} ${activeCategory === key ? styles.activeFilter : ''}`}
                        onClick={() => setActiveCategory(key)}
                     >
                        <Icon size={18} /> {type.label}
                     </div>
                  );
               })}
            </div>
         </div>

         {/* Main Content */}
         <div className={styles.main}>
            {/* Search Bar */}
            <div className={styles.searchBar}>
               <div className={styles.searchInputWrapper}>
                  <Search size={16} className={styles.searchIcon} />
                  <input 
                     className={styles.searchInput} 
                     placeholder="Search files..." 
                     value={searchQuery}
                     onChange={(e) => setSearchQuery(e.target.value)}
                  />
               </div>
            </div>

            {/* Upload Zone */}
            <div 
               className={`${styles.uploadZone} ${isDragging ? styles.dragActive : ''}`}
               onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
               onDragLeave={() => setIsDragging(false)}
               onDrop={(e) => { e.preventDefault(); setIsDragging(false); handleUpload(e.dataTransfer.files); }}
               onClick={() => fileInputRef.current?.click()}
            >
               <div className={styles.uploadIcon}>
                  <UploadCloud size={32} className={styles.uploadIconSvg} />
               </div>
               <div>
                  <div className={styles.uploadText}>Drop files here to upload</div>
                  <div className={styles.uploadSub}>or click to browse</div>
               </div>
            </div>

            {/* Content Area */}
            <div className={styles.contentArea}>
               {isLoading ? (
                  <div className={styles.loadingState}>Loading files...</div>
               ) : files.length === 0 ? (
                  <div className={styles.emptyState}>No files found.</div>
               ) : viewMode === 'grid' ? (
                  /* Grid View */
                  <div className={styles.grid}>
                     {files.map(file => (
                        <div 
                           key={file.id} 
                           className={`${styles.fileCard} ${selectedIds.has(file.id) ? styles.cardSelected : ''}`}
                           onClick={() => setPreviewFile(file)}
                        >
                           <input 
                              type="checkbox" 
                              className={styles.checkbox}
                              checked={selectedIds.has(file.id)}
                              onClick={(e) => { e.stopPropagation(); toggleSelection(file.id); }}
                              onChange={() => {}}
                           />
                           
                           <div style={{position: 'relative'}}>
                               <button 
                                  className={styles.moreBtn} 
                                  onClick={(e) => { 
                                     e.stopPropagation(); 
                                     setOpenMenuId(openMenuId === file.id ? null : file.id);
                                  }}
                               >
                                  <MoreVertical size={16} />
                               </button>
                               {openMenuId === file.id && (
                                  <div className={styles.contextMenu} onClick={e => e.stopPropagation()}>
                                      <div className={styles.menuItem} onClick={() => window.open(file.url, '_blank')}>
                                          <Download size={14} /> Download
                                      </div>
                                      <div className={styles.menuItem} onClick={() => copyLink(file.id)}>
                                          <Copy size={14} /> Copy Link
                                      </div>
                                      <div className={`${styles.menuItem} ${styles.menuDelete}`} onClick={() => deleteMutation.mutate(file.id)}>
                                          <Trash2 size={14} /> Delete
                                      </div>
                                  </div>
                               )}
                           </div>

                           <div className={styles.preview}>
                              {file.mime_type?.startsWith('image/') ? (
                                 <img src={file.url} alt={file.name} className={styles.previewImg} />
                              ) : getFileIcon(file.mime_type)}
                           </div>
                           
                           <div className={styles.fileInfo}>
                              <div className={styles.fileName} title={file.name}>{file.name}</div>
                              <div className={styles.fileMeta}>
                                 <span>{formatSize(file.size)}</span>
                                 <span>{new Date(file.uploaded_at).toLocaleDateString()}</span>
                              </div>
                           </div>
                        </div>
                     ))}
                  </div>
               ) : (
                  /* List View */
                  <table className={styles.table}>
                     <thead>
                        <tr>
                           <th style={{width:'40px'}}><input type="checkbox" /></th>
                           <th>Name</th>
                           <th>Size</th>
                           <th>Owner</th>
                           <th>Date</th>
                           <th></th>
                        </tr>
                     </thead>
                     <tbody>
                        {files.map(file => (
                           <tr 
                              key={file.id} 
                              className={`${styles.row} ${selectedIds.has(file.id) ? styles.rowSelected : ''}`}
                              onClick={() => setPreviewFile(file)}
                           >
                              <td onClick={e => e.stopPropagation()}>
                                 <input 
                                    type="checkbox" 
                                    checked={selectedIds.has(file.id)}
                                    onChange={() => toggleSelection(file.id)}
                                 />
                              </td>
                              <td>
                                 <div className={styles.listNameCell}>
                                    {getFileIcon(file.mime_type)}
                                    <span className={styles.listNameText}>{file.name}</span>
                                 </div>
                              </td>
                              <td>{formatSize(file.size)}</td>
                              <td>
                                 <div className={styles.listOwnerCell}>
                                    <Avatar src={file.uploaded_by?.avatar} fallback="U" size="xs" />
                                    <span>{file.uploaded_by?.username || 'Me'}</span>
                                 </div>
                              </td>
                              <td>{new Date(file.uploaded_at).toLocaleDateString()}</td>
                              <td style={{position:'relative'}}>
                                 <button 
                                    className={styles.moreBtn} 
                                    style={{position:'static', opacity: 1}}
                                    onClick={(e) => { 
                                       e.stopPropagation(); 
                                       setOpenMenuId(openMenuId === file.id ? null : file.id);
                                    }}
                                 >
                                    <MoreVertical size={16}/>
                                 </button>
                                 {openMenuId === file.id && (
                                    <div className={styles.contextMenu} style={{top:'2rem', right:'1rem', zIndex: 50}} onClick={e => e.stopPropagation()}>
                                        <div className={styles.menuItem} onClick={() => window.open(file.url, '_blank')}>
                                            <Download size={14} /> Download
                                        </div>
                                        <div className={`${styles.menuItem} ${styles.menuDelete}`} onClick={() => deleteMutation.mutate(file.id)}>
                                            <Trash2 size={14} /> Delete
                                        </div>
                                    </div>
                                 )}
                              </td>
                           </tr>
                        ))}
                     </tbody>
                  </table>
               )}
            </div>
         </div>
      </div>

      {/* Bulk Actions */}
      {selectedIds.size > 0 && (
         <div className={styles.bulkBar}>
            <span className={styles.bulkText}>{selectedIds.size} selected</span>
            <div className={styles.bulkActions}>
               <button className={styles.actionBtn}><Download size={16} /> Download</button>
               <button 
                  className={`${styles.actionBtn} ${styles.deleteBtn}`} 
                  onClick={() => { if(confirm('Delete selected?')) bulkDeleteMutation.mutate(Array.from(selectedIds)); }}
               >
                  <Trash2 size={16} /> Delete
               </button>
            </div>
         </div>
      )}

      {/* Preview Modal */}
      {previewFile && (
         <div className={styles.modalOverlay} onClick={() => setPreviewFile(null)}>
            <div className={styles.previewModal} onClick={e => e.stopPropagation()}>
               <div className={styles.previewContent}>
                  <button className={styles.closePreview} onClick={() => setPreviewFile(null)}>
                     <X size={24} />
                  </button>
                  {previewFile.mime_type?.startsWith('image/') ? (
                     <img src={previewFile.url} alt={previewFile.name} className={styles.fullImage} />
                  ) : (
                     <div className={styles.previewFallback}>
                        {getFileIcon(previewFile.mime_type)}
                        <p className={styles.previewFallbackText}>Preview not available for this file type</p>
                     </div>
                  )}
               </div>
               <div className={styles.previewSidebar}>
                  <div className={styles.previewHeader}>
                     <div className={styles.previewIconBox}>{getFileIcon(previewFile.mime_type)}</div>
                     <div className={styles.previewTitleBox}>
                        <h3 className={styles.previewTitle} title={previewFile.name}>{previewFile.name}</h3>
                        <p className={styles.previewSize}>{formatSize(previewFile.size)}</p>
                     </div>
                  </div>

                  <div className={styles.previewMeta}>
                     <div className={styles.previewMetaRow}>
                        <span>Uploaded by</span>
                        <span className={styles.previewMetaValue}>{previewFile.uploaded_by?.username || 'Me'}</span>
                     </div>
                     <div className={styles.previewMetaRow}>
                        <span>Date</span>
                        <span className={styles.previewMetaValue}>{new Date(previewFile.uploaded_at).toLocaleDateString()}</span>
                     </div>
                  </div>

                  <div className={styles.previewActions}>
                     <Button className={styles.fullWidthBtn} onClick={() => window.open(previewFile.url, '_blank')}>
                        <Download size={16} className={styles.iconMr} /> Download
                     </Button>
                     <Button variant="ghost" className={styles.shareBtn}>
                        <Share2 size={16} className={styles.iconMr} /> Share Link
                     </Button>
                     <Button 
                        variant="ghost" 
                        className={styles.dangerBtn}
                        onClick={() => deleteMutation.mutate(previewFile.id)}
                     >
                        <Trash2 size={16} className={styles.iconMr} /> Delete
                     </Button>
                  </div>
               </div>
            </div>
         </div>
      )}
    </div>
  );
};

export default FileManager;