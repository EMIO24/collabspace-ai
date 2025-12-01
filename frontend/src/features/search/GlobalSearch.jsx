import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ArrowRight, User as UserIcon } from 'lucide-react';
import { api } from '../../services/api';
import Avatar from '../../components/ui/Avatar/Avatar';
import ProfileSlideOver from './ProfileSlideOver';
import styles from './SearchModal.module.css';

// Debounce hook to prevent excessive API calls
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
};

const GlobalSearch = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUserId, setSelectedUserId] = useState(null);
  const debouncedSearch = useDebounce(searchTerm, 300);

  // Toggle with Cmd+K or Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
        if (!isOpen) {
          setSearchTerm('');
        }
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
        setSelectedUserId(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  // Fetch Logic
  const { data: results, isLoading } = useQuery({
    queryKey: ['globalSearch', debouncedSearch],
    queryFn: async () => {
      if (!debouncedSearch) return [];
      const res = await api.get(`/auth/users/search/?q=${debouncedSearch}`);
      return res.data;
    },
    enabled: !!debouncedSearch,
    initialData: []
  });

  const handleUserClick = (uuid) => {
    setSelectedUserId(uuid);
    setIsOpen(false); // Close search to focus on profile
  };

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={styles.overlay}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
          >
            <motion.div
              className={styles.modal}
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className={styles.header}>
                <Search className={styles.searchIcon} size={20} />
                <input
                  autoFocus
                  className={styles.input}
                  placeholder="Search team members..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <div className={styles.resultsList}>
                {!debouncedSearch && (
                  <div className={styles.emptyState}>
                    Type to search for colleagues, managers, and contributors.
                  </div>
                )}

                {debouncedSearch && isLoading && (
                   <div className={styles.emptyState}>Searching...</div>
                )}

                {debouncedSearch && !isLoading && results.length === 0 && (
                  <div className={styles.emptyState}>No users found.</div>
                )}

                {results.map((user) => (
                  <div
                    key={user.id}
                    className={styles.resultItem}
                    onClick={() => handleUserClick(user.id)}
                  >
                    <Avatar src={user.avatar} fallback={user.username[0]} size="md" />
                    <div className={styles.userInfo}>
                      <div className={styles.userName}>
                        {user.first_name} {user.last_name}
                      </div>
                      <div className={styles.userEmail}>{user.email}</div>
                    </div>
                    <ArrowRight size={16} className={styles.arrowIcon} />
                  </div>
                ))}
              </div>

              <div className={styles.footer}>
                <div className={styles.shortcut}>
                  <span className={styles.key}><UserIcon size={10} /></span>
                  <span>Users</span>
                </div>
                <div className={styles.shortcut}>
                  <span>Navigate</span>
                  <span className={styles.key}>↑</span>
                  <span className={styles.key}>↓</span>
                </div>
                <div className={styles.shortcut}>
                  <span>Select</span>
                  <span className={styles.key}>↵</span>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <ProfileSlideOver 
        userId={selectedUserId} 
        onClose={() => setSelectedUserId(null)} 
      />
    </>
  );
};

export default GlobalSearch;