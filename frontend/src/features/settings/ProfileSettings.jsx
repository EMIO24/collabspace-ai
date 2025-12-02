import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Avatar from '../../components/ui/Avatar/Avatar';
import Input from '../../components/ui/Input/Input';
import Button from '../../components/ui/Button/Button';
import styles from './ProfileSettings.module.css';

const ProfileSettings = () => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    first_name: '', last_name: '', email: '', bio: ''
  });

  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => (await api.get('/auth/profile/')).data,
  });

  useEffect(() => {
    if (profile) {
      setFormData({
        first_name: profile.first_name || '',
        last_name: profile.last_name || '',
        email: profile.email || '',
        bio: profile.bio || ''
      });
    }
  }, [profile]);

  const updateMutation = useMutation({
    mutationFn: (data) => api.put('/auth/profile/', data),
    onSuccess: () => {
      queryClient.invalidateQueries(['profile']);
      toast.success('Profile updated');
    },
    onError: () => toast.error('Failed to update profile')
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <div className={styles.header}>
        <h2 className={styles.title}>My Profile</h2>
        <p className={styles.subtitle}>Manage your personal information and public profile.</p>
      </div>

      <div className={styles.avatarSection}>
        <Avatar src={profile?.avatar} size="lg" style={{ width: '6rem', height: '6rem', fontSize: '2rem' }} />
        <div className={styles.avatarActions}>
          <Button variant="ghost" style={{ border: '1px solid var(--glass-border)' }}>Change Avatar</Button>
          <p className={styles.avatarHelp}>JPG, GIF or PNG. Max size of 2MB</p>
        </div>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); updateMutation.mutate(formData); }}>
        <div className={styles.formGrid}>
          <Input 
            label="First Name" 
            value={formData.first_name}
            onChange={e => setFormData({...formData, first_name: e.target.value})}
          />
          <Input 
            label="Last Name" 
            value={formData.last_name}
            onChange={e => setFormData({...formData, last_name: e.target.value})}
          />
        </div>

        <div className={styles.formGroup}>
          <Input 
            label="Email Address" 
            value={formData.email}
            disabled 
            style={{ backgroundColor: 'rgba(0,0,0,0.05)', cursor: 'not-allowed' }}
          />
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label}>Bio</label>
          <textarea
            className={styles.textArea}
            rows={4}
            value={formData.bio}
            onChange={e => setFormData({...formData, bio: e.target.value})}
          />
        </div>

        <div className={styles.actions}>
          <Button type="submit" isLoading={updateMutation.isPending}>
            Save Changes
          </Button>
        </div>
      </form>
    </div>
  );
};

export default ProfileSettings;