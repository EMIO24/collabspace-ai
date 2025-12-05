import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { 
  CheckCircle, Folder, MessageSquare, Clock, 
  Check, UploadCloud, PlusCircle, FileText
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Badge from '../../components/ui/Badge/Badge';
import Avatar from '../../components/ui/Avatar/Avatar';
import styles from './ProfileDashboard.module.css';
import CreateProjectModal from '../projects/CreateProjectModal';

const ProfileDashboard = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('all');
  const [showProjectModal, setShowProjectModal] = useState(false);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  // --- DATA FETCHING ---
  const { data: user } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      try {
        const res = await api.get('/auth/profile/');
        return res.data;
      } catch (e) {
        return null;
      }
    }
  });

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: async () => {
      try {
        const res = await api.get('/auth/stats/');
        return res.data;
      } catch {
        return { tasks_completed: 0, active_projects: 0, unread_messages: 0, hours_tracked: 0 };
      }
    }
  });

  const { data: rawProjects, isLoading: loadingProjects } = useQuery({
    queryKey: ['recentProjects'],
    queryFn: async () => {
      try {
        const res = await api.get('/projects/?limit=6');
        return res.data;
      } catch { return []; }
    }
  });

  const projects = useMemo(() => {
    if (!rawProjects) return [];
    const list = Array.isArray(rawProjects) ? rawProjects : (rawProjects?.results || []);
    return list.map((p, idx) => ({
      ...p,
      style: ['gradientPurple', 'gradientBlue', 'gradientIndigo'][idx % 3]
    }));
  }, [rawProjects]);

  const { data: rawTasks, isLoading: loadingTasks } = useQuery({
    queryKey: ['myTasks', user?.id],
    queryFn: async () => {
      if (!user?.id) return [];
      try {
        const res = await api.get(`/tasks/tasks/?assigned_to=${user.id}`);
        return res.data;
      } catch { return []; }
    },
    enabled: !!user?.id
  });

  const allTasks = useMemo(() => {
    if (!rawTasks) return [];
    const list = Array.isArray(rawTasks) ? rawTasks : (rawTasks?.results || []);
    return list;
  }, [rawTasks]);

  const { data: rawActivity, isLoading: loadingActivity } = useQuery({
    queryKey: ['dashboardActivity'],
    queryFn: async () => {
      try {
        const res = await api.get('/auth/activity/feed/');
        return res.data;
      } catch { return []; }
    }
  });

  const activity = useMemo(() => {
    const list = Array.isArray(rawActivity) ? rawActivity : (rawActivity?.results || []);
    if (list.length === 0 && !loadingActivity) {
      return [
        { id: 1, description: 'Alice commented on "Homepage Redesign"', created_at: new Date().toISOString(), type: 'comment' },
        { id: 2, description: 'Bob uploaded "Q3 Report.pdf"', created_at: new Date(Date.now() - 3600000).toISOString(), type: 'file' },
        { id: 3, description: 'You created project "Mobile App"', created_at: new Date(Date.now() - 7200000).toISOString(), type: 'create' },
      ];
    }
    return list;
  }, [rawActivity, loadingActivity]);

  const filteredTasks = useMemo(() => {
    const today = new Date().toISOString().split('T')[0];
    return allTasks.filter(task => {
      if (task.status === 'done') return false; 
      if (activeTab === 'today') return task.due_date === today;
      if (activeTab === 'overdue') return task.due_date < today;
      return true;
    }).slice(0, 5);
  }, [allTasks, activeTab]);

  const completeMutation = useMutation({
    mutationFn: (taskId) => api.patch(`/tasks/tasks/${taskId}/`, { status: 'done' }),
    onSuccess: () => {
      toast.success('Task completed');
      queryClient.invalidateQueries(['myTasks']);
      queryClient.invalidateQueries(['dashboardStats']);
    },
    onError: () => toast.error('Failed to update task')
  });

  const formatDuration = (mins) => {
    if (!mins) return '0h';
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return `${h}h ${m}m`;
  };

  const getActivityIcon = (text) => {
    const lower = (text || '').toLowerCase();
    if (lower.includes('upload') || lower.includes('file')) return <UploadCloud size={14} />;
    if (lower.includes('comment')) return <MessageSquare size={14} />;
    if (lower.includes('complete') || lower.includes('done')) return <CheckCircle size={14} />;
    return <FileText size={14} />;
  };

  return (
    <div className={styles.container}>
      <div className={styles.banner}>
        <div className={styles.bannerContent}>
          <h1 className={styles.greeting}>{getGreeting()}, {user?.first_name || 'User'}!</h1>
          <p className={styles.greetingSub}>
             You have {allTasks.filter(t => t.due_date === new Date().toISOString().split('T')[0]).length} urgent tasks due today.
          </p>
          <button className={styles.createBtn} onClick={() => setShowProjectModal(true)}>
            <PlusCircle size={18} /> Create new project
          </button>
        </div>
        <div className={styles.bannerDecoration} />
      </div>

      <div className={styles.statsGrid}>
        <StatCard label="Tasks Completed" value={stats?.tasks_completed} icon={CheckCircle} color="green" onClick={() => navigate('/tasks')} trend="+12%" />
        <StatCard label="Active Projects" value={stats?.active_projects} icon={Folder} color="blue" onClick={() => navigate('/projects')} />
        <StatCard label="Messages" value={stats?.unread_messages} icon={MessageSquare} color="orange" onClick={() => navigate('/chat')} />
        <StatCard label="Time Tracked" value={formatDuration(stats?.hours_tracked)} icon={Clock} color="purple" onClick={() => navigate('/analytics')} />
      </div>

      <div className={styles.mainSplit}>
        <div className={styles.leftCol}>
          <div>
            <div className={styles.projectsHeader}>
              <h2 className={styles.sectionTitle}>Recent Projects</h2>
              <span className={styles.viewAllLink} onClick={() => navigate('/projects')}>View All</span>
            </div>
            
            {loadingProjects ? (
              <div className={styles.loadingProjects}>
                 <div className={`${styles.skeletonCard} ${styles.projectSkeleton}`} />
                 <div className={`${styles.skeletonCard} ${styles.projectSkeleton}`} />
                 <div className={`${styles.skeletonCard} ${styles.projectSkeleton}`} />
              </div>
            ) : (
              <div className={styles.projectsGrid}>
                {projects.slice(0, 3).map((project) => (
                  <div 
                    key={project.id} 
                    className={`${styles.projectCard} ${styles[project.style]}`}
                    onClick={() => navigate(`/projects/${project.id}`)}
                  >
                    <div>
                      <div className={styles.projectTitle}>{project.name}</div>
                      <div className={styles.progressTrack}>
                        <div className={styles.progressFill} style={{ width: `${project.progress || 0}%` }} />
                      </div>
                    </div>
                    <div className={styles.projectFooter}>
                       <div className={styles.teamStack}>
                          {[1,2,3].map(i => (
                            <div key={i} className={styles.teamAvatar}>U</div>
                          ))}
                       </div>
                       <span style={{fontSize:'0.8rem', fontWeight:700}}>{project.progress || 0}%</span>
                    </div>
                  </div>
                ))}
                {!projects.length && <div className={`${styles.emptyState} ${styles.colSpan3}`}>No recent projects.</div>}
              </div>
            )}
          </div>

          <div className={styles.tasksContainer}>
            <div className={styles.tasksHeader}>
                <h3 className={styles.tasksTitle}>My Tasks</h3>
                <div className={styles.taskTabs}>
                    {['all', 'today', 'overdue'].map(tab => (
                        <button key={tab} className={`${styles.tabBtn} ${activeTab === tab ? styles.activeTab : ''}`} onClick={() => setActiveTab(tab)}>
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                    ))}
                </div>
            </div>
            
            <div className={styles.taskList}>
                {loadingTasks ? (
                   <div className={styles.loadingTasks}>
                     {[1,2,3].map(i => <div key={i} className={`${styles.skeleton} ${styles.taskSkeleton}`} />)}
                   </div>
                ) : filteredTasks.map(task => (
                    <div key={task.id} className={styles.taskRow}>
                        <div className={styles.taskCheckbox} onClick={() => completeMutation.mutate(task.id)}>
                            {task.status === 'done' && <Check size={14} />}
                        </div>
                        <span className={styles.taskText} onClick={() => navigate(`/projects/${task.project}/board`)}>
                            {task.title}
                        </span>
                        <div className={`${styles.priorityDot} ${styles[`dot${task.priority ? (task.priority.charAt(0).toUpperCase() + task.priority.slice(1)) : 'Low'}`]}`} />
                        <span className={`${styles.taskDate} ${new Date(task.due_date) < new Date() ? styles.dateOverdue : ''}`}>
                            {task.due_date ? new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : ''}
                        </span>
                    </div>
                ))}
                {!filteredTasks.length && !loadingTasks && <div className={styles.emptyState}>No tasks found.</div>}
            </div>
          </div>
        </div>

        <div className={styles.activityContainer}>
           <h2 className={styles.activityTitle}>Activity Feed</h2>
           <div className={styles.activityList}>
             {loadingActivity ? (
                <div className={styles.loadingTasks}>
                  {[1,2,3].map(i => <div key={i} className={`${styles.skeleton} ${styles.taskSkeleton}`} />)}
                </div>
             ) : activity.map((item, i) => (
                <div key={item.id || i} className={styles.activityItem}>
                   <div className={styles.activityDot} />
                   <div className={styles.activityContent}>
                      <div className={styles.activityHeader}>
                        {getActivityIcon(item.description)}
                        <span className={styles.activityUser}>{item.user_name || 'User'}</span>
                      </div>
                      {item.description}
                   </div>
                   <span className={styles.activityTime}>
                      {item.created_at ? new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                   </span>
                </div>
             ))}
             {!activity.length && !loadingActivity && <div className={styles.emptyState}>No recent activity.</div>}
           </div>
        </div>
      </div>

      {showProjectModal && <CreateProjectModal onClose={() => setShowProjectModal(false)} />}
    </div>
  );
};

const StatCard = ({ label, value, icon: Icon, color, onClick }) => (
    <div className={styles.statCard} onClick={onClick}>
        <div className={styles.statHeader}>
            <div className={`${styles.iconBox} ${styles[`theme-${color}`]}`}>
              <Icon size={24} />
            </div>
        </div>
        <div>
            <div className={styles.statValue}>{value || 0}</div>
            <div className={styles.statLabel}>{label}</div>
        </div>
    </div>
);

export default ProfileDashboard;