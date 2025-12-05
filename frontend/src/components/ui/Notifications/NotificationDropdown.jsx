import React, { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell, X } from 'lucide-react';
import { api } from '../../../services/api';
import styles from './NotificationDropdown.module.css';

const NotificationDropdown = ({ onClose }) => {
  const queryClient = useQueryClient();

  const { data: rawData } = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => (await api.get('/notifications/')).data
  });

  const notifications = useMemo(() => {
    if (!rawData) return [];
    if (Array.isArray(rawData)) return rawData;
    if (rawData.results && Array.isArray(rawData.results)) return rawData.results;
    return [];
  }, [rawData]);

  const readMutation = useMutation({
    mutationFn: (id) => api.post(`/notifications/${id}/mark_as_read/`),
    onSuccess: () => queryClient.invalidateQueries(['notifications'])
  });

  return (
    <div className={styles.dropdown}>
      <div className={styles.header}>
        <span>Notifications</span>
        <button onClick={onClose} className={styles.closeBtn}>
          <X size={16} />
        </button>
      </div>
      
      <div className={styles.list}>
        {notifications.map(notif => (
          <div 
            key={notif.id} 
            className={`${styles.item} ${!notif.is_read ? styles.itemUnread : ''}`}
            onClick={() => readMutation.mutate(notif.id)}
          >
            <div className={styles.icon}>
              <Bell size={16} fill={notif.is_read ? "none" : "currentColor"} />
            </div>
            <div>
              <p className={styles.message}>{notif.message}</p>
              <p className={styles.time}>{new Date(notif.created_at).toLocaleString()}</p>
            </div>
          </div>
        ))}
        {!notifications.length && (
          <div className={styles.empty}>All caught up!</div>
        )}
      </div>
    </div>
  );
};

export default NotificationDropdown;