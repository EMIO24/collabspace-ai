import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Mail, Calendar, Shield } from 'lucide-react';
import { api } from '../../services/api';
import Avatar from '../../components/ui/Avatar/Avatar';
import Badge from '../../components/ui/Badge/Badge';
import Button from '../../components/ui/Button/Button';
import styles from './ProfileSlideOver.module.css';

const ProfileSlideOver = ({ userId, onClose }) => {
  const { data: user, isLoading } = useQuery({
    queryKey: ['userProfile', userId],
    queryFn: async () => {
      if (!userId) return null;
      const res = await api.get(`/auth/users/${userId}/`);
      return res.data;
    },
    enabled: !!userId,
  });

  return (
    <AnimatePresence>
      {userId && (
        <motion.div
          className={styles.backdrop}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className={styles.panel}
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className={styles.header}>
              <h2 className={styles.title}>User Profile</h2>
              <button className={styles.closeButton} onClick={onClose}>
                <X size={20} />
              </button>
            </div>

            {isLoading ? (
              <div className={styles.loadingContainer}>
                 <div className={styles.spinner}></div>
              </div>
            ) : user ? (
              <div className={styles.content}>
                <Avatar 
                  src={user.avatar} 
                  alt={user.username} 
                  size="lg" 
                  className={styles.avatar}
                />
                
                <div className={styles.userInfo}>
                  <h3 className={styles.name}>
                    {user.first_name} {user.last_name}
                  </h3>
                  <p className={styles.username}>@{user.username}</p>
                </div>

                <div className={styles.badges}>
                   <Badge variant={user.is_active ? 'success' : 'gray'}>
                     {user.is_active ? 'Active' : 'Inactive'}
                   </Badge>
                   <Badge variant="purple">Team Member</Badge>
                </div>

                <div className={styles.statsRow}>
                  <div className={styles.statItem}>
                    <span className={styles.statValue}>{user.projects_count || 0}</span>
                    <span className={styles.statLabel}>Projects</span>
                  </div>
                  <div className={styles.statItem}>
                    <span className={styles.statValue}>{user.tasks_count || 0}</span>
                    <span className={styles.statLabel}>Tasks</span>
                  </div>
                </div>

                <div className={styles.detailsList}>
                  <div className={styles.detailItem}>
                    <Mail size={18} className={styles.iconBlue} />
                    <span>{user.email}</span>
                  </div>
                  <div className={styles.detailItem}>
                    <Shield size={18} className={styles.iconPurple} />
                    <span>Role: {user.role || 'Contributor'}</span>
                  </div>
                  <div className={styles.detailItem}>
                    <Calendar size={18} className={styles.iconOrange} />
                    <span>Joined: {new Date(user.date_joined).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className={styles.actionFooter}>
                  <Button className={styles.fullButton} variant="primary">Message User</Button>
                </div>
              </div>
            ) : null}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ProfileSlideOver;