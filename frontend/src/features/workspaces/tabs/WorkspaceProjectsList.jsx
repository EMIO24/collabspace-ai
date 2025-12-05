import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Plus, FolderPlus } from 'lucide-react';
import { api } from '../../../services/api';
import ProjectCard from '../../projects/ProjectCard';
import CreateProjectModal from '../../projects/CreateProjectModal';
import Button from '../../../components/ui/Button/Button';
import styles from './WorkspaceProjectsList.module.css';

const WorkspaceProjectsList = ({ workspaceId }) => {
  const navigate = useNavigate();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // 1. Fetch Projects for this Workspace
  const { data: rawData, isLoading } = useQuery({
    queryKey: ['workspaceProjects', workspaceId],
    queryFn: async () => {
      const res = await api.get(`/projects/?workspace=${workspaceId}`);
      return res.data;
    },
    enabled: !!workspaceId
  });

  // 2. Data Normalization
  const projects = useMemo(() => {
    if (!rawData) return [];
    if (Array.isArray(rawData)) return rawData;
    if (rawData.results && Array.isArray(rawData.results)) return rawData.results;
    return [];
  }, [rawData]);

  const handleProjectClick = (projectId) => {
    navigate(`/projects/${projectId}`);
  };

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading projects...</div>;

  return (
    <div className={styles.container}>
      <div className={styles.toolbar}>
        <h3 className={styles.title}>Workspace Projects ({projects.length})</h3>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus size={16} style={{ marginRight: '0.5rem' }} /> New Project
        </Button>
      </div>

      <div className={styles.grid}>
        {projects.map((project) => (
          <ProjectCard 
            key={project.id} 
            project={project} 
            onClick={() => handleProjectClick(project.id)} 
          />
        ))}

        {!projects.length && (
          <div className={styles.emptyState}>
            <FolderPlus size={48} className={styles.emptyIcon} />
            <h4 className={styles.emptyText}>No projects yet</h4>
            <p className={styles.emptySub}>Start by creating a project for your team.</p>
            <Button variant="ghost" onClick={() => setIsCreateModalOpen(true)}>
              Create First Project
            </Button>
          </div>
        )}
      </div>

      {isCreateModalOpen && (
        <CreateProjectModal onClose={() => setIsCreateModalOpen(false)} />
      )}
    </div>
  );
};

export default WorkspaceProjectsList;