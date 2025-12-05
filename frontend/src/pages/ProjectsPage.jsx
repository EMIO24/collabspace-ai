import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Trash2, Archive, CheckSquare, Filter, FolderPlus } from 'lucide-react';
import { api } from '../services/api';
import { useNavigate } from 'react-router-dom';
import ProjectCard from '../features/projects/ProjectCard';
import CreateProjectModal from '../features/projects/CreateProjectModal';
import Button from '../components/ui/Button/Button';
import styles from './ProjectsPage.module.css';
import { toast } from 'react-hot-toast';

const FILTERS = ['All', 'Active', 'On Hold', 'Completed'];

const ProjectsPage = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeFilter, setActiveFilter] = useState('All');
  const [sortBy, setSortBy] = useState('-updated_at');
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());

  // 1. Fetch Projects with Filters
  const { data: rawProjects, isLoading } = useQuery({
    queryKey: ['projects', activeFilter, sortBy, search],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (activeFilter !== 'All') params.append('status', activeFilter.toLowerCase().replace(' ', '_'));
      if (search) params.append('search', search);
      params.append('ordering', sortBy);
      
      const res = await api.get(`/projects/?${params.toString()}`);
      return res.data;
    }
  });

  const projects = useMemo(() => {
    if (!rawProjects) return [];
    const list = Array.isArray(rawProjects) ? rawProjects : (rawProjects?.results || []);
    return list;
  }, [rawProjects]);

  // 2. Bulk Selection Logic
  const toggleSelection = (id) => {
    const newSet = new Set(selectedIds);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedIds(newSet);
  };

  const bulkDeleteMutation = useMutation({
    mutationFn: async (ids) => {
      // Parallel delete requests
      await Promise.all(ids.map(id => api.delete(`/projects/${id}/`)));
    },
    onSuccess: () => {
      toast.success(`Deleted ${selectedIds.size} projects`);
      setSelectedIds(new Set());
      queryClient.invalidateQueries(['projects']);
    }
  });

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Projects</h1>
          <p className={styles.subtitle}>Manage your team's initiatives and goals.</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus size={18} className="mr-2" /> New Project
        </Button>
      </div>

      {/* Toolbar */}
      <div className={styles.toolbar}>
        <div className={styles.filters}>
          {FILTERS.map(f => (
            <button
              key={f}
              className={`${styles.filterChip} ${activeFilter === f ? styles.activeChip : ''}`}
              onClick={() => setActiveFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>

        <div className={styles.actions}>
          <div className={styles.searchWrapper}>
             <Search size={16} className={styles.searchIcon} />
             <input 
               className={styles.searchInput} 
               placeholder="Search projects..." 
               value={search}
               onChange={(e) => setSearch(e.target.value)}
             />
          </div>
          <select 
            className={styles.select}
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="-updated_at">Last Updated</option>
            <option value="name">Alphabetical</option>
            <option value="due_date">Due Date</option>
            <option value="-progress">Progress</option>
          </select>
        </div>
      </div>

      {/* Grid View */}
      <div className={styles.grid}>
        {isLoading ? (
          <div className="col-span-full text-center py-20 text-gray-400">Loading projects...</div>
        ) : projects.length > 0 ? (
          projects.map(project => (
            <ProjectCard
              key={project.id}
              project={project}
              onClick={() => navigate(`/projects/${project.id}`)}
              selectable={true}
              selected={selectedIds.has(project.id)}
              onSelect={() => toggleSelection(project.id)}
            />
          ))
        ) : (
          <div className={styles.emptyState}>
            <FolderPlus size={64} className="mx-auto mb-4 opacity-20" />
            <h3 className="text-xl font-bold text-gray-700">No projects found</h3>
            <p className="text-gray-500 mb-6">Get started by creating your first project.</p>
            <Button variant="ghost" onClick={() => setIsModalOpen(true)}>Create Project</Button>
          </div>
        )}
      </div>

      {/* Floating Bulk Actions */}
      {selectedIds.size > 0 && (
        <div className={styles.bulkBar}>
          <div className={styles.bulkInfo}>
            <CheckSquare size={18} className="text-blue-400" />
            {selectedIds.size} selected
          </div>
          <div className={styles.bulkActions}>
            <button 
               className={`${styles.bulkBtn} ${styles.deleteBtn}`} 
               onClick={() => {
                 if(confirm(`Delete ${selectedIds.size} projects?`)) 
                   bulkDeleteMutation.mutate(Array.from(selectedIds));
               }}
            >
              <Trash2 size={16} /> Delete
            </button>
            <button className={styles.bulkBtn} onClick={() => setSelectedIds(new Set())}>
               Cancel
            </button>
          </div>
        </div>
      )}

      {isModalOpen && <CreateProjectModal onClose={() => setIsModalOpen(false)} />}
    </div>
  );
};

export default ProjectsPage;