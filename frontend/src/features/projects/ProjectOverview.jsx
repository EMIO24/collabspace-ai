import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Settings, Calendar, CheckCircle2, Clock, Layers } from 'lucide-react';
import { api } from '../../services/api';

// Components
import Button from '../../components/ui/Button/Button';
import Badge from '../../components/ui/Badge/Badge';
import Avatar from '../../components/ui/Avatar/Avatar';
import BurndownChart from '../analytics/BurndownChart';
import ProjectActivity from './ProjectActivity';

import styles from './ProjectOverview.module.css';

const ProjectOverview = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  // 1. Fetch Project Details
  const { data: project, isLoading: loadingProject } = useQuery({
    queryKey: ['project', id],
    queryFn: async () => {
      const res = await api.get(`/projects/${id}/`);
      return res.data;
    },
    enabled: !!id
  });

  // 2. Fetch Stats
  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['projectStats', id],
    queryFn: async () => {
      const res = await api.get(`/projects/${id}/stats/`);
      return res.data; // Expected: { total_tasks: 20, completed: 15, days_remaining: 5, progress: 75 }
    },
    enabled: !!id
  });

  // 3. Fetch Team
  const { data: members, isLoading: loadingMembers } = useQuery({
    queryKey: ['projectMembers', id],
    queryFn: async () => {
      const res = await api.get(`/projects/${id}/members/`);
      return res.data;
    },
    enabled: !!id
  });

  if (loadingProject || loadingStats || loadingMembers) {
    return <div className="p-8 text-center text-gray-500">Loading Project Dashboard...</div>;
  }

  if (!project) return <div>Project not found</div>;

  const progress = stats?.progress || 0;

  return (
    <div className={styles.container}>
      {/* --- HEADER --- */}
      <div className={styles.header}>
        <div className={styles.headerTop}>
          <div className={styles.titleGroup}>
            <h1 className={styles.title}>
              {project.name}
              <Badge variant={project.status === 'active' ? 'success' : 'gray'}>
                {project.status || 'Active'}
              </Badge>
            </h1>
            <div className={styles.dates}>
              <Calendar size={14} />
              <span>
                {new Date(project.start_date).toLocaleDateString()} — {new Date(project.end_date).toLocaleDateString()}
              </span>
            </div>
          </div>
          <Button 
            variant="ghost" 
            onClick={() => navigate(`/projects/${id}/settings`)}
          >
            <Settings size={18} className="mr-2" />
            Settings
          </Button>
        </div>

        {/* Progress Bar */}
        <div className={styles.progressWrapper}>
          <div className={styles.progressHeader}>
            <span>Project Completion</span>
            <span>{progress}%</span>
          </div>
          <div className={styles.progressTrack}>
            <div className={styles.progressFill} style={{ width: `${progress}%` }} />
          </div>
        </div>
      </div>

      {/* --- MAIN GRID --- */}
      <div className={styles.grid}>
        
        {/* LEFT COLUMN: Stats & Charts */}
        <div className={styles.leftColumn}>
          {/* Stats Row */}
          <div className={styles.statsRow}>
            <div className={styles.statCard}>
              <span className={styles.statValue}>{stats?.total_tasks || 0}</span>
              <span className={styles.statLabel}>
                <Layers size={14} style={{ display: 'inline', marginRight: '4px' }}/> 
                Total Tasks
              </span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: 'var(--success)' }}>
                {stats?.completed || 0}
              </span>
              <span className={styles.statLabel}>
                <CheckCircle2 size={14} style={{ display: 'inline', marginRight: '4px' }}/> 
                Completed
              </span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: 'var(--warning)' }}>
                {stats?.days_remaining || 0}
              </span>
              <span className={styles.statLabel}>
                <Clock size={14} style={{ display: 'inline', marginRight: '4px' }}/> 
                Days Left
              </span>
            </div>
          </div>

          {/* Burndown Chart */}
          <BurndownChart projectId={id} />
        </div>

        {/* RIGHT COLUMN: Team & Activity */}
        <div className={styles.rightColumn}>
          
          {/* Team Members */}
          <div className={styles.sectionCard}>
            <div className={styles.sectionHeader}>
              <h3 className={styles.sectionTitle}>Team Members</h3>
              <span className="text-xs text-gray-400">{members?.length || 0} Members</span>
            </div>
            <div className={styles.teamList}>
              {members?.map((member) => (
                <div key={member.id} className={styles.memberItem}>
                  <Avatar 
                    src={member.avatar} 
                    fallback={member.username[0]} 
                    size="sm" 
                  />
                  <div className={styles.memberInfo}>
                    <span className={styles.memberName}>
                      {member.first_name} {member.last_name}
                    </span>
                    <span className={styles.memberRole}>
                      {member.role || 'Contributor'}
                    </span>
                  </div>
                </div>
              ))}
              {(!members || members.length === 0) && (
                <div className="text-sm text-gray-500 text-center py-2">No members yet.</div>
              )}
            </div>
          </div>

          {/* Activity Feed (Reused Component) */}
          <div className={styles.sectionCard}>
            <div className={styles.sectionHeader}>
              <h3 className={styles.sectionTitle}>Recent Activity</h3>
            </div>
            {/* We pass the ID to the existing component which fetches its own data */}
            <ProjectActivity projectId={id} />
          </div>

        </div>
      </div>
    </div>
  );
};

export default ProjectOverview;