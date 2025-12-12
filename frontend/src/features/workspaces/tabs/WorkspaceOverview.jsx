import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { 
  FolderOpen, CheckCircle, Users, Activity, Plus, UserPlus, BarChart3
} from 'lucide-react';
import { api } from '../../../services/api';
import Avatar from '../../../components/ui/Avatar/Avatar';
import Button from '../../../components/ui/Button/Button';
import styles from './WorkspaceOverview.module.css';

const WorkspaceOverview = ({ workspaceId, onTabChange }) => {
  const navigate = useNavigate();

  // 1. Fetch Stats
  const { data: stats } = useQuery({
    queryKey: ['workspaceStats', workspaceId],
    queryFn: async () => {
      try {
         const res = await api.get(`/analytics/workspace/${workspaceId}/metrics/?range=30d`);
         return {
            projects: res.data.overview?.total_projects || 0,
            members: res.data.overview?.total_members || 0,
            tasks: res.data.overview?.total_tasks || 0,
            health: res.data.overview?.activity_rate || 0
         };
      } catch (e) {
         const basicRes = await api.get(`/workspaces/${workspaceId}/`);
         return {
            projects: basicRes.data.project_count || 0,
            members: basicRes.data.member_count || 0,
            tasks: 0,
            health: 0
         };
      }
    }
  });

  // 2. Fetch Recent Projects (Rename data to rawProjects)
  const { data: rawProjects } = useQuery({
    queryKey: ['workspaceProjects', workspaceId],
    queryFn: async () => {
      const res = await api.get(`/projects/?workspace=${workspaceId}&limit=5`);
      return res.data; 
    }
  });

  // FIX: Data Normalization
  const projects = useMemo(() => {
    if (!rawProjects) return [];
    if (Array.isArray(rawProjects)) return rawProjects;
    if (rawProjects.results && Array.isArray(rawProjects.results)) return rawProjects.results;
    return [];
  }, [rawProjects]);

  // 3. Fetch Activity
  const { data: rawActivity } = useQuery({
    queryKey: ['workspaceActivity', workspaceId],
    queryFn: async () => {
       try { return (await api.get('/auth/activity/feed/')).data; } 
       catch { return []; }
    }
  });

  // FIX: Data Normalization for Activity
  const timeline = useMemo(() => {
      if (!rawActivity) return [];
      const list = Array.isArray(rawActivity) ? rawActivity : (rawActivity.results || []);
      return list.slice(0, 5);
  }, [rawActivity]);

  return (
    <div className={styles.grid}>
      {/* --- LEFT COL --- */}
      <div className={styles.mainCol}>
         
         {/* Stats Grid */}
         <div className={styles.statsGrid}>
            <StatCard label="Total Projects" value={stats?.projects || 0} icon={FolderOpen} color="blue" />
            <StatCard label="Total Tasks" value={stats?.tasks || 0} icon={CheckCircle} color="green" />
            <StatCard label="Team Members" value={stats?.members || 0} icon={Users} color="orange" />
            <StatCard label="Activity Rate" value={`${stats?.health || 0}%`} icon={Activity} color="purple" />
         </div>

         {/* Active Projects */}
         <div className={styles.card}>
            <div className={styles.cardHeader}>
               <h3 className={styles.cardTitle}>Active Projects</h3>
               <button className={styles.linkBtn} onClick={() => onTabChange('Projects')}>View All →</button>
            </div>
            <div className={styles.projectList}>
               {projects.map(project => (
                  <div key={project.id} className={styles.projectRow} onClick={() => navigate(`/projects/${project.id}`)}>
                     <div className={styles.projectIcon}>{project.name ? project.name[0].toUpperCase() : 'P'}</div>
                     <div className={styles.projectInfo}>
                        <div className={styles.projectName}>{project.name}</div>
                        <div className={styles.progressBar}>
                           <div className={styles.progressFill} style={{width: `${project.progress || 0}%`}} />
                        </div>
                     </div>
                     <div className={styles.projectMeta}>
                        <span className={styles.statusBadge}>{project.status}</span>
                        <span className={styles.date}>{new Date(project.updated_at).toLocaleDateString()}</span>
                     </div>
                  </div>
               ))}
               {!projects.length && <div className={styles.emptyState}>No projects yet.</div>}
            </div>
         </div>
      </div>

      {/* --- RIGHT COL --- */}
      <div className={styles.sideCol}>
         
         {/* Quick Actions */}
         <div className={styles.card}>
            <h3 className={styles.cardTitle}>Quick Actions</h3>
            <div className={styles.actionList}>
               <button className={styles.actionBtn} onClick={() => onTabChange('Projects')}>
                  <Plus size={16} /> Create Project
               </button>
               <button className={styles.actionBtn} onClick={() => onTabChange('Members')}>
                  <UserPlus size={16} /> Invite Member
               </button>
               <button className={styles.actionBtn} onClick={() => onTabChange('Analytics')}>
                  <BarChart3 size={16} /> View Analytics
               </button>
            </div>
         </div>

         {/* Activity Timeline */}
         <div className={styles.card}>
            <h3 className={styles.cardTitle}>Recent Activity</h3>
            <div className={styles.timeline}>
               {timeline.map((item, i) => (
                  <div key={i} className={styles.timelineItem}>
                     <div className={styles.timelineDot} />
                     <div className={styles.timelineContent}>
                        <p className={styles.timelineText}>
                           <strong>{item.user_name || 'User'}</strong> {item.description}
                        </p>
                        <span className={styles.timelineTime}>
                           {new Date(item.created_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
                        </span>
                     </div>
                  </div>
               ))}
               {!timeline.length && <div className={styles.emptyState}>No recent activity.</div>}
            </div>
         </div>

      </div>
    </div>
  );
};

const StatCard = ({ label, value, icon: Icon, color }) => (
   <div className={styles.statCard}>
      <div className={`${styles.iconBox} ${styles[color]}`}>
         <Icon size={20} />
      </div>
      <div>
         <div className={styles.statValue}>{value}</div>
         <div className={styles.statLabel}>{label}</div>
      </div>
   </div>
);

export default WorkspaceOverview;