import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Bell, Mail, Smartphone, Clock, Moon } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import styles from './NotificationSettings.module.css';

const Toggle = ({ label, checked, onChange, description }) => (
  <div className={styles.toggleRow}>
    <div>
       <span className={styles.toggleLabel}>{label}</span>
       {description && <p className={styles.toggleDesc}>{description}</p>}
    </div>
    <label className={styles.switch}>
      <input type="checkbox" checked={checked} onChange={onChange} />
      <span className={styles.slider}></span>
    </label>
  </div>
);

const NotificationSettings = () => {
  const [prefs, setPrefs] = useState({
    email_assignments: true,
    email_mentions: true,
    push_mentions: true,
    dnd_enabled: false,
    dnd_start: '18:00',
    dnd_end: '09:00',
    frequency: 'realtime' // realtime, hourly, daily
  });

  useQuery({
    queryKey: ['notificationPrefs'],
    queryFn: async () => {
      try {
        const res = await api.get('/notifications/preferences/');
        if (res.data) setPrefs(res.data);
        return res.data;
      } catch { return null; }
    }
  });

  const mutation = useMutation({
    mutationFn: (newPrefs) => api.put('/notifications/preferences/', newPrefs),
    onSuccess: () => toast.success('Preferences saved')
  });

  const updatePref = (key, val) => {
    const newPrefs = { ...prefs, [key]: val };
    setPrefs(newPrefs);
    mutation.mutate(newPrefs);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Notifications</h2>
        <p className={styles.subtitle}>Choose how and when you want to be notified.</p>
      </div>

      <div className={styles.grid}>
        <div className={styles.card}>
           <div className={styles.cardHeader}>
              <h3 className={styles.cardTitle}><Mail size={18} className="text-blue-500"/> Email & Push</h3>
           </div>
           <div className={styles.content}>
              <Toggle 
                 label="Task Assignments" 
                 description="When a task is assigned to you"
                 checked={prefs.email_assignments} 
                 onChange={() => updatePref('email_assignments', !prefs.email_assignments)} 
              />
              <Toggle 
                 label="Mentions" 
                 description="When someone @mentions you"
                 checked={prefs.email_mentions} 
                 onChange={() => updatePref('email_mentions', !prefs.email_mentions)} 
              />
              
              <div className="mt-4 pt-4 border-t border-gray-100">
                 <label className={styles.label}>Frequency</label>
                 <select 
                    className={styles.select}
                    value={prefs.frequency}
                    onChange={(e) => updatePref('frequency', e.target.value)}
                 >
                    <option value="realtime">Real-time (Immediate)</option>
                    <option value="hourly">Hourly Digest</option>
                    <option value="daily">Daily Summary (9:00 AM)</option>
                 </select>
              </div>
           </div>
        </div>

        <div className={styles.card}>
           <div className={styles.cardHeader}>
              <h3 className={styles.cardTitle}><Moon size={18} className="text-purple-500"/> Do Not Disturb</h3>
           </div>
           <div className={styles.content}>
              <Toggle 
                 label="Enable DND Schedule" 
                 checked={prefs.dnd_enabled} 
                 onChange={() => updatePref('dnd_enabled', !prefs.dnd_enabled)} 
              />
              
              {prefs.dnd_enabled && (
                <div className="mt-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
                   <div className="flex items-center gap-4 mb-3">
                      <div className="flex-1">
                         <label className="text-xs font-bold text-gray-500 block mb-1">Start Time</label>
                         <input 
                           type="time" 
                           className={styles.timeInput}
                           value={prefs.dnd_start}
                           onChange={(e) => updatePref('dnd_start', e.target.value)}
                         />
                      </div>
                      <div className="flex-1">
                         <label className="text-xs font-bold text-gray-500 block mb-1">End Time</label>
                         <input 
                           type="time" 
                           className={styles.timeInput}
                           value={prefs.dnd_end}
                           onChange={(e) => updatePref('dnd_end', e.target.value)}
                         />
                      </div>
                   </div>
                   <p className="text-xs text-gray-400">Notifications will be paused during these hours.</p>
                </div>
              )}
              
              <button 
                 className={styles.testBtn} 
                 onClick={() => toast('Test Notification sent!')}
              >
                 <Bell size={14}/> Send Test Notification
              </button>
           </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationSettings;