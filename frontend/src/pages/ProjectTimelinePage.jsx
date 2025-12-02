import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useInfiniteQuery } from '@tanstack/react-query';
import { 
  History, 
  CheckCircle2, 
  MessageSquare, 
  FileText, 
  AlertCircle, 
  ArrowRight, 
  Filter 
} from 'lucide-react';
import { api } from '../services/api';
import Avatar from '../components/ui/Avatar/Avatar';
import Button from '../components/ui/Button/Button';
import styles from './ProjectTimelinePage.module.css';

const EVENT_ICONS = {
  task_update: { icon: CheckCircle2, style: styles.type_task },
  comment: { icon: MessageSquare, style: styles.type_comment },
  file_upload: { icon: FileText, style: styles.type_file },
  alert: { icon: AlertCircle, style: styles.type_alert },
  completion: { icon: CheckCircle2, style: styles.type_success }
};

const ProjectTimelinePage = () => {
  const { id } = useParams();
  const [filterUser, setFilterUser] = useState('');
  const [filterType, setFilterType] = useState('');

  // Infinite Scroll Query
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading
  } = useInfiniteQuery({
    queryKey: ['projectActivity', id, filterUser, filterType],
    queryFn: async ({ pageParam = 1 }) => {
      const params = new URLSearchParams({
        page: pageParam,
        user: filterUser,
        type: filterType
      });
      const res = await api.get(`/projects/${id}/activity/?${params.toString()}`);
      return res.data; 
    },
    getNextPageParam: (lastPage) => lastPage.next || undefined,
    enabled: !!id
  });

  const allEvents = data?.pages.flatMap(page => page.results) || [];

  const handleLoadMore = () => {
    fetchNextPage();
  };

  const getEventConfig = (type) => {
    return EVENT_ICONS[type] || { icon: History, style: '' };
  };

  return (
    <div className={styles.container}>
      {/* --- HEADER --- */}
      <div className={styles.header}>
        <div className={styles.titleRow}>
          <div>
            <h1 className={styles.title}>
              <History size={28} className="text-blue-600" />
              Audit Log & Activity
            </h1>
            <p className={styles.subtitle}>Track every change, comment, and update in this project.</p>
          </div>
        </div>

        <div className={styles.toolbar}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
            <Filter size={16} />
            <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>Filter by:</span>
          </div>
          
          <select 
            className={styles.filterSelect}
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="">All Events</option>
            <option value="task_update">Task Updates</option>
            <option value="comment">Comments</option>
            <option value="file_upload">Files</option>
          </select>

          <select 
            className={styles.filterSelect}
            value={filterUser}
            onChange={(e) => setFilterUser(e.target.value)}
          >
            <option value="">All Users</option>
            <option value="current">My Activity</option>
          </select>
        </div>
      </div>

      {/* --- TIMELINE --- */}
      <div className={styles.timelineWrapper}>
        <div className={styles.timelineLine} />

        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading history...</div>
        ) : allEvents.length > 0 ? (
          allEvents.map((event) => {
            const { icon: Icon, style } = getEventConfig(event.type);
            
            return (
              <div key={event.id} className={styles.eventRow}>
                {/* Icon Column */}
                <div className={styles.iconWrapper}>
                  <div className={`${styles.iconCircle} ${style}`}>
                    <Icon size={18} />
                  </div>
                </div>

                {/* Content Card */}
                <div className={styles.eventCard}>
                  <div className={styles.eventHeader}>
                    <Avatar 
                      src={event.user.avatar} 
                      fallback={event.user.username[0]} 
                      size="sm" 
                    />
                    <div>
                      <span className={styles.eventUser}>{event.user.username}</span>
                      <span className={styles.eventAction}> {event.description}</span>
                    </div>
                    <span className={styles.eventTime}>
                      {new Date(event.timestamp).toLocaleString()}
                    </span>
                  </div>

                  {/* Diff View (if applicable) */}
                  {event.diff && (
                    <div className={styles.diffContainer}>
                      <div className={styles.diffItem}>
                        <span className={styles.diffLabel}>{event.diff.field}</span>
                        <span className={styles.oldValue}>{event.diff.old}</span>
                        <ArrowRight size={12} className="text-gray-400" />
                        <span className={styles.newValue}>{event.diff.new}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-10 text-gray-500">
            No activity found for these filters.
          </div>
        )}
      </div>

      {/* --- LOAD MORE --- */}
      <div className={styles.footer}>
        <Button 
          variant="ghost" 
          onClick={handleLoadMore} 
          disabled={!hasNextPage || isFetchingNextPage}
        >
          {isFetchingNextPage ? 'Loading...' : hasNextPage ? 'Load Older Activity' : 'End of History'}
        </Button>
      </div>
    </div>
  );
};

export default ProjectTimelinePage;