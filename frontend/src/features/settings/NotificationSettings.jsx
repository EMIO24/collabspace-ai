import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Bell, Mail, Smartphone } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import styles from './NotificationSettings.module.css';

const Toggle = ({ label, checked, onChange, icon: Icon }) => (
  <div className={styles.toggleRow}>
    <div className={styles.toggleInfo}>
      {Icon && <div className={styles.iconBox}><Icon size={18} /></div>}
      <span className={styles.label}>{label}</span>
    </div>
    <label className={styles.switch}>
      <input type="checkbox" checked={checked} onChange={onChange} />
      <span className={styles.slider}></span>
    </label>
  </div>
);

const NotificationSettings = () => {
  const [prefs, setPrefs] = useState({
    email_project_updates: true,
    email_mentions: true,
    push_mentions: true,
    weekly_digest: false
  });

  useQuery({
    queryKey: ['notificationPrefs'],
    queryFn: async () => {
      const res = await api.get('/notifications/preferences/');
      setPrefs(res.data);
      return res.data;
    }
  });

  const mutation = useMutation({
    mutationFn: (newPrefs) => api.put('/notifications/preferences/', newPrefs),
    onSuccess: () => toast.success('Preferences saved')
  });

  const handleToggle = (key) => {
    const newPrefs = { ...prefs, [key]: !prefs[key] };
    setPrefs(newPrefs);
    mutation.mutate(newPrefs);
  };

  return (
    <div>
      <div className={styles.pageHeader}>
        <h2 className={styles.title}>Notifications</h2>
        <p className={styles.subtitle}>Choose how and when you want to be notified.</p>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionHeader}>Email Notifications</h3>
        <Toggle 
          label="Project Updates & Status Changes" 
          icon={Mail}
          checked={prefs.email_project_updates} 
          onChange={() => handleToggle('email_project_updates')} 
        />
        <Toggle 
          label="Mentions & Comments" 
          icon={Mail}
          checked={prefs.email_mentions} 
          onChange={() => handleToggle('email_mentions')} 
        />
        <Toggle 
          label="Weekly Productivity Digest" 
          icon={Mail}
          checked={prefs.weekly_digest} 
          onChange={() => handleToggle('weekly_digest')} 
        />
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionHeader}>Push Notifications</h3>
        <Toggle 
          label="Direct Mentions (@user)" 
          icon={Smartphone}
          checked={prefs.push_mentions} 
          onChange={() => handleToggle('push_mentions')} 
        />
      </div>
    </div>
  );
};

export default NotificationSettings;