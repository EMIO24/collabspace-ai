import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, Folder } from 'lucide-react';
import { api } from '../services/api';
import { useWorkspace } from '../context/WorkspaceContext';
import ProjectCard from '../features/projects/ProjectCard';
import CreateProjectModal from '../features/projects/CreateProjectModal';
import Button from '../components/ui/Button/Button';
import styles from './ProjectsPage.module.css';

const ProjectsPage = () => {
  const { currentWorkspace } = useWorkspace();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects', currentWorkspace?.id],
    queryFn: async () => {
      if (!currentWorkspace) return [];
      const res = await api.get(`/projects/?workspace=${currentWorkspace.id}`);
      return res.data;
    },
    enabled: !!currentWorkspace
  });

  const handleProjectClick = (projectId) => {
    // In a real router, navigate here: navigate(`/projects/${projectId}`);
    console.log('Navigate to project:', projectId);
  };

  if (!currentWorkspace) {
    return (
      <div className={styles.container}>
        <div className={styles.emptyState}>
          <Folder size={48} className="text-gray-300" />
          <h3 className={styles.emptyTitle}>No Workspace Selected</h3>
          <p className={styles.emptyDesc}>Please select or create a workspace from the sidebar to view projects.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.heading}>Projects</h1>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus size={18} />
          New Project
        </Button>
      </div>

      <div className={styles.grid}>
        {isLoading ? (
          // Skeleton loaders
          [1, 2, 3, 4].map((i) => (
            <div 
              key={i} 
              className="animate-pulse bg-white/20 rounded-2xl h-64 border border-white/30"
            />
          ))
        ) : projects && projects.length > 0 ? (
          projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onClick={() => handleProjectClick(project.id)}
            />
          ))
        ) : (
          <div className={styles.emptyState}>
            <Folder size={48} className="text-gray-300" />
            <h3 className={styles.emptyTitle}>No projects yet</h3>
            <p className={styles.emptyDesc}>
              Get started by creating your first project in <strong>{currentWorkspace.name}</strong>.
            </p>
          </div>
        )}
      </div>

      {isModalOpen && (
        <CreateProjectModal onClose={() => setIsModalOpen(false)} />
      )}
    </div>
  );
};

export default ProjectsPage;