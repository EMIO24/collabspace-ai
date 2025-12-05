import React, { useState } from 'react';
import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { api } from '../../../services/api';
import { Globe, Smartphone, Bot } from 'lucide-react'; 
import styles from './WorkspaceOverview.module.css';

const WorkspaceOverview = ({ workspaceId, onTabChange }) => {
  const [activityFilter, setActivityFilter] = useState('all');

  // 1. Fetch Stats
  const { data: stats } = useQuery({
    queryKey: ['workspaceStats', workspaceId],
    queryFn: async () => (await api.get(`/workspaces/${workspaceId}/stats/`)).data,
  });

  // 2. Fetch Active Projects
  const { data: rawProjects, isLoading: loadingProjects } = useQuery({
    queryKey: ['workspaceActiveProjects', workspaceId],
    queryFn: async () => {
      const res = await api.get(`/projects/?workspace=${workspaceId}&limit=5`);
      return res.data;
    }
  });

  const projects = Array.isArray(rawProjects) ? rawProjects : (rawProjects?.results || []);

  // 3. Fetch Activity (Infinite Scroll)
  const {
    data: activityData,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading: loadingActivity
  } = useInfiniteQuery({
    queryKey: ['workspaceActivity', workspaceId, activityFilter],
    queryFn: async ({ pageParam = 1 }) => {
      // Append filter type if not 'all'
      const typeParam = activityFilter !== 'all' ? `&type=${activityFilter}` : '';
      const res = await api.get(`/workspaces/${workspaceId}/activity/?page=${pageParam}${typeParam}`);
      return res.data; 
    },
    getNextPageParam: (lastPage) => lastPage.next ? lastPage.next : undefined,
    enabled: !!workspaceId
  });

  const activities = activityData?.pages.flatMap(page => page.results) || [];

  const getProjectIcon = (name) => {
    const lower = name.toLowerCase();
    if (lower.includes('web')) return <Globe size={20} className="text-blue-500" />;
    if (lower.includes('app')) return <Smartphone size={20} className="text-purple-500" />;
    return <Bot size={20} className="text-green-500" />;
  };

  return (
    <div className={styles.container}>
      
      {/* Quick Stats */}
      <div>
        <h3 className={styles.sectionTitle}>Quick Stats</h3>
        <div className={styles.statsGrid}>
          <div className={styles.statCard} onClick={() => onTabChange('Projects')}>
            <div className={styles.statValue}>{stats?.active_projects || 0}</div>
            <div className={styles.statLabel}>Projects</div>
          </div>
          <div className={styles.statCard} onClick={() => onTabChange('Analytics')}>
            <div className={styles.statValue}>{stats?.completed_tasks || 0}</div>
            <div className={styles.statLabel}>Tasks</div>
          </div>
          <div className={styles.statCard} onClick={() => onTabChange('Members')}>
            <div className={styles.statValue}>{stats?.members_count || 0}</div>
            <div className={styles.statLabel}>Members</div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statValue}>{stats?.health_score || '100'}%</div>
            <div className={styles.statLabel}>Health</div>
          </div>
        </div>
      </div>

      {/* Split View */}
      <div className={styles.splitGrid}>
        
        {/* Active Projects */}
        <div>
          <h3 className={styles.sectionTitle}>Active Projects</h3>
          <div className={styles.projectList}>
            {loadingProjects ? (
              <div className="p-4 text-gray-400">Loading...</div>
            ) : projects.length > 0 ? (
              projects.map(p => (
                <div key={p.id} className={styles.projectRow} onClick={() => onTabChange('Projects')}>
                  <div className={styles.projectInfo}>
                    <div className={styles.projectName}>
                      {getProjectIcon(p.name)}
                      {p.name}
                    </div>
                    <div className={styles.projectBar}>
                      <div className={styles.projectFill} style={{ width: `${p.progress || 0}%` }} />
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="font-bold text-blue-600 text-sm">{p.progress || 0}%</span>
                    <span className={styles.projectDue}>
                       {p.end_date ? `Due: ${new Date(p.end_date).toLocaleDateString()}` : 'No Due Date'}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className={styles.emptyState}>No active projects found.</div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className={styles.sectionTitle} style={{marginBottom:0}}>Recent Activity</h3>
          </div>
          
          {/* Filters */}
          <div className={styles.filterBar}>
             {['all', 'task', 'project', 'member'].map(f => (
               <button 
                 key={f}
                 className={`${styles.filterBtn} ${activityFilter === f ? styles.activeFilter : ''}`}
                 onClick={() => setActivityFilter(f)}
               >
                 {f.charAt(0).toUpperCase() + f.slice(1)}s
               </button>
             ))}
          </div>

          <div className={styles.activityList}>
            {loadingActivity ? (
               <div className="p-4 text-gray-400">Loading...</div>
            ) : activities.length > 0 ? (
              activities.map((act, i) => (
                <div key={act.id || i} className={styles.activityItem}>
                  <div className={`${styles.dot} ${styles.purpleDot}`} />
                  <p className={styles.activityText}>
                    {act.description}
                  </p>
                  <span className={styles.activityTime}>
                    {act.created_at ? new Date(act.created_at).toLocaleString() : 'Just now'}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-sm text-gray-400">No recent activity.</div>
            )}

            {/* Load More */}
            {hasNextPage && (
              <button 
                className={styles.loadMoreBtn} 
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
              >
                {isFetchingNextPage ? 'Loading...' : 'Load More'}
              </button>
            )}
          </div>
        </div>

      </div>

    </div>
  );
};

export default WorkspaceOverview;