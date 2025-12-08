import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import { User, Lock, Trash2, Camera, Save, Download, Github, Linkedin, Twitter } from 'lucide-react';
import Button from '../../components/ui/Button/Button';
import Avatar from '../../components/ui/Avatar/Avatar';
import styles from './ProfileSettings.module.css';

const ProfileSettings = () => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef(null);
  
  const [formData, setFormData] = useState({
    first_name: '', last_name: '', email: '', bio: '', job_title: '', location: '',
    social_github: '', social_linkedin: '', social_twitter: ''
  });
  
  const [passwordData, setPasswordData] = useState({
    current_password: '', new_password: '', confirm_password: ''
  });
  
  const [deleteConfirm, setDeleteConfirm] = useState('');

  // Data Fetching
  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => (await api.get('/auth/profile/')).data,
  });

  const { data: stats } = useQuery({
    queryKey: ['accountStats'],
    queryFn: async () => (await api.get('/auth/stats/')).data
  });

  useEffect(() => {
    if (profile) {
      setFormData({
        first_name: profile.first_name || '',
        last_name: profile.last_name || '',
        email: profile.email || '',
        bio: profile.bio || '',
        job_title: profile.job_title || '',
        location: profile.location || '',
        social_github: profile.social_github || '',
        social_linkedin: profile.social_linkedin || '',
        social_twitter: profile.social_twitter || ''
      });
    }
  }, [profile]);

  // Mutations
  const updateProfile = useMutation({
    mutationFn: (data) => api.put('/auth/profile/', data),
    onSuccess: () => {
      queryClient.invalidateQueries(['profile']);
      toast.success('Profile updated successfully');
    }
  });

  const changePassword = useMutation({
    mutationFn: (data) => api.post('/auth/change-password/', data),
    onSuccess: () => {
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
      toast.success('Password changed');
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to change password')
  });

  const uploadAvatar = useMutation({
    mutationFn: (file) => {
      const formData = new FormData();
      formData.append('avatar', file);
      // Assuming PUT profile handles multipart, otherwise use separate endpoint
      return api.put('/auth/profile/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['profile']);
      toast.success('Avatar updated');
    }
  });

  const deleteAccount = useMutation({
    mutationFn: () => api.delete('/auth/account/'),
    onSuccess: () => {
      localStorage.removeItem('accessToken');
      window.location.href = '/login';
    }
  });

  // Handlers
  const handleFileSelect = (e) => {
    if (e.target.files?.[0]) uploadAvatar.mutate(e.target.files[0]);
  };

  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      return toast.error("New passwords don't match");
    }
    changePassword.mutate(passwordData);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Account Settings</h2>
        <p className={styles.subtitle}>Manage your personal information and security.</p>
      </div>

      {/* --- Profile Section --- */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <h3 className={styles.cardTitle}><User size={20} className="text-blue-500"/> Personal Info</h3>
        </div>
        
        <div className={styles.avatarSection}>
          <div className={styles.avatarWrapper} onClick={() => fileInputRef.current?.click()}>
            <Avatar src={profile?.avatar} size="lg" fallback={profile?.username?.[0]} className="w-full h-full text-4xl" />
            <div className={styles.avatarOverlay}>
              <Camera size={24} />
            </div>
            <input type="file" hidden ref={fileInputRef} onChange={handleFileSelect} accept="image/*" />
          </div>
          <div>
             <div className="font-bold text-lg text-gray-800">Profile Photo</div>
             <div className="text-sm text-gray-500">Click to upload a new avatar. Max 2MB.</div>
          </div>
        </div>

        <form onSubmit={(e) => { e.preventDefault(); updateProfile.mutate(formData); }}>
          <div className={styles.formGrid}>
            <div>
              <label className={styles.label}>First Name</label>
              <input className={styles.input} value={formData.first_name} onChange={e => setFormData({...formData, first_name: e.target.value})} />
            </div>
            <div>
              <label className={styles.label}>Last Name</label>
              <input className={styles.input} value={formData.last_name} onChange={e => setFormData({...formData, last_name: e.target.value})} />
            </div>
            <div className={styles.fullWidth}>
              <label className={styles.label}>Email Address</label>
              <input className={styles.input} value={formData.email} disabled style={{background: '#f1f5f9', cursor: 'not-allowed'}} />
            </div>
            <div>
              <label className={styles.label}>Job Title</label>
              <input className={styles.input} value={formData.job_title} onChange={e => setFormData({...formData, job_title: e.target.value})} />
            </div>
            <div>
              <label className={styles.label}>Location</label>
              <input className={styles.input} value={formData.location} onChange={e => setFormData({...formData, location: e.target.value})} />
            </div>
            <div className={styles.fullWidth}>
              <label className={styles.label}>Bio</label>
              <textarea 
                className={styles.textarea} 
                value={formData.bio} 
                onChange={e => setFormData({...formData, bio: e.target.value})}
                maxLength={500}
              />
              <span className={styles.charCount}>{formData.bio.length}/500</span>
            </div>
            
            {/* Social Links */}
            <div className={styles.fullWidth}>
               <label className={styles.label} style={{marginTop:'1rem'}}>Social Profiles</label>
               <div className="grid grid-cols-3 gap-4">
                  <div className="relative">
                     <Github size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                     <input className={styles.input} style={{paddingLeft:'2.5rem'}} placeholder="GitHub URL" value={formData.social_github} onChange={e => setFormData({...formData, social_github: e.target.value})} />
                  </div>
                  <div className="relative">
                     <Linkedin size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                     <input className={styles.input} style={{paddingLeft:'2.5rem'}} placeholder="LinkedIn URL" value={formData.social_linkedin} onChange={e => setFormData({...formData, social_linkedin: e.target.value})} />
                  </div>
                  <div className="relative">
                     <Twitter size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                     <input className={styles.input} style={{paddingLeft:'2.5rem'}} placeholder="Twitter URL" value={formData.social_twitter} onChange={e => setFormData({...formData, social_twitter: e.target.value})} />
                  </div>
               </div>
            </div>
          </div>
          
          <div className={styles.actions}>
            <Button type="button" variant="ghost">Cancel</Button>
            <Button type="submit" isLoading={updateProfile.isPending}>Save Changes</Button>
          </div>
        </form>
      </div>

      {/* --- Password Section --- */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <h3 className={styles.cardTitle}><Lock size={20} className="text-purple-500"/> Change Password</h3>
        </div>
        <form onSubmit={handlePasswordSubmit} className="max-w-md space-y-4">
          <div>
            <label className={styles.label}>Current Password</label>
            <input className={styles.input} type="password" value={passwordData.current_password} onChange={e => setPasswordData({...passwordData, current_password: e.target.value})} required />
          </div>
          <div>
            <label className={styles.label}>New Password</label>
            <input className={styles.input} type="password" value={passwordData.new_password} onChange={e => setPasswordData({...passwordData, new_password: e.target.value})} required />
          </div>
          <div>
            <label className={styles.label}>Confirm New Password</label>
            <input className={styles.input} type="password" value={passwordData.confirm_password} onChange={e => setPasswordData({...passwordData, confirm_password: e.target.value})} required />
          </div>
          <div className="flex justify-end pt-2">
            <Button type="submit" isLoading={changePassword.isPending}>Update Password</Button>
          </div>
        </form>
      </div>

      {/* --- Account Stats --- */}
      <div className={styles.statsRow}>
         <div className={styles.miniStat}>
            <span className={styles.statVal}>{stats?.total_tasks || 0}</span>
            <span className={styles.statLabel}>Tasks</span>
         </div>
         <div className={styles.miniStat}>
            <span className={styles.statVal}>{stats?.total_projects || 0}</span>
            <span className={styles.statLabel}>Projects</span>
         </div>
         <div className={styles.miniStat}>
            <span className={styles.statVal}>{stats?.total_hours || 0}h</span>
            <span className={styles.statLabel}>Logged</span>
         </div>
         <div className={styles.miniStat} style={{ border: 'none' }}>
            <button className="flex items-center gap-2 text-sm font-bold text-gray-600 hover:text-blue-600 transition-colors">
               <Download size={16} /> Download Data
            </button>
         </div>
      </div>

      {/* --- Danger Zone --- */}
      <div className={styles.dangerZone}>
         <div className={styles.cardHeader} style={{borderBottomColor:'#fecaca'}}>
            <h3 className={`${styles.cardTitle} ${styles.dangerTitle}`}><Trash2 size={20}/> Delete Account</h3>
         </div>
         <p className="text-sm text-red-900 mb-6">
            This action is permanent. All your data, projects, and tasks will be wiped immediately.
         </p>
         <div className={styles.dangerActions}>
            <input 
               className={styles.confirmInput} 
               placeholder="Type DELETE to confirm"
               value={deleteConfirm}
               onChange={e => setDeleteConfirm(e.target.value)}
            />
            <button 
               className={styles.deleteBtn}
               disabled={deleteConfirm !== 'DELETE'}
               onClick={() => deleteAccount.mutate()}
            >
               Delete Account
            </button>
         </div>
      </div>
    </div>
  );
};

export default ProfileSettings;