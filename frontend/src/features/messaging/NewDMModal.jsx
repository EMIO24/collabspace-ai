import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Search, UserPlus } from 'lucide-react';
import { api } from '../../services/api';
import { toast } from 'react-hot-toast';
import Avatar from '../../components/ui/Avatar/Avatar';
import styles from './NewDMModal.module.css';

const NewDMModal = ({ onClose, onDmCreated }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const queryClient = useQueryClient();

  // 1. Search Users
  const { data: users, isLoading } = useQuery({
    queryKey: ['userSearch', searchQuery],
    queryFn: async () => {
      if (!searchQuery) return [];
      const res = await api.get(`/auth/users/search/?q=${searchQuery}`);
      return res.data;
    },
    enabled: searchQuery.length > 1
  });

  // 2. Create/Get DM Mutation
  const createDmMutation = useMutation({
    mutationFn: (userId) => api.post('/messaging/direct-messages/', { recipient: userId }),
    onSuccess: (res) => {
      // API should return the DM object { id, ... }
      queryClient.invalidateQueries(['directMessages']);
      toast.success('Conversation started');
      if (onDmCreated) onDmCreated(res.data.id);
      onClose();
    },
    onError: () => {
      toast.error('Failed to start conversation');
    }
  });

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <h3 className={styles.title}>New Message</h3>
          <button className={styles.closeBtn} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className={styles.searchSection}>
          <div className="relative">
             <input 
               className={styles.searchInput}
               placeholder="Type a name or email..."
               value={searchQuery}
               onChange={(e) => setSearchQuery(e.target.value)}
               autoFocus
             />
             <Search size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" />
          </div>
        </div>

        <div className={styles.resultsList}>
          {isLoading ? (
            <div className={styles.loading}>Searching...</div>
          ) : users && users.length > 0 ? (
            users.map(user => (
              <div 
                key={user.id} 
                className={styles.userItem}
                onClick={() => createDmMutation.mutate(user.id)}
              >
                <Avatar src={user.avatar} fallback={user.username[0]} size="md" />
                <div className={styles.userInfo}>
                  <div className={styles.userName}>{user.first_name} {user.last_name}</div>
                  <div className={styles.userEmail}>@{user.username}</div>
                </div>
                <div className={`${styles.statusDot} ${user.is_online ? styles.online : ''}`} />
              </div>
            ))
          ) : searchQuery.length > 1 ? (
            <div className={styles.empty}>No users found.</div>
          ) : (
            <div className={styles.empty}>Start typing to find people...</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NewDMModal;