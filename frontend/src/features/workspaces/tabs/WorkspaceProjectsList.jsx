import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Grid, List, FolderPlus } from 'lucide-react';
import { api } from '../../../services/api';
import Button from '../../../components/ui/Button/Button';
import ProjectCard from '../../projects/ProjectCard'; // Reusing existing card
import CreateProjectModal from '../../projects/CreateProjectModal'; // Reusing existing modal

const WorkspaceProjectsList = ({ workspaceId }) => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState('grid');
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: projects, isLoading } = useQuery({
    queryKey: ['workspaceProjects', workspaceId, search],
    queryFn: async () => {
      const res = await api.get(`/projects/?workspace=${workspaceId}&search=${search}`);
      return Array.isArray(res.data) ? res.data : (res.data.results || []);
    },
    enabled: !!workspaceId
  });

  const gridStyle = {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
      gap: '1.5rem',
      marginTop: '1.5rem'
  };

  const listStyle = {
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
      marginTop: '1.5rem'
  };

  if (isLoading) return <div style={{padding:'3rem', textAlign:'center', color:'#9ca3af'}}>Loading projects...</div>;

  return (
    <div>
       <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'2rem' }}>
          <div style={{ position:'relative', width:'300px' }}>
             <Search size={16} style={{position:'absolute', left:'1rem', top:'50%', transform:'translateY(-50%)', color:'#9ca3af'}} />
             <input 
                placeholder="Search projects..." 
                value={search}
                onChange={e => setSearch(e.target.value)}
                style={{ width:'100%', padding:'0.7rem 1rem 0.7rem 2.8rem', borderRadius:'10px', border:'1px solid #e2e8f0', outline:'none' }}
             />
          </div>
          <div style={{ display:'flex', gap:'1rem' }}>
             <div style={{ display:'flex', background:'#f1f5f9', padding:'4px', borderRadius:'8px' }}>
                <button 
                  onClick={() => setViewMode('grid')}
                  style={{ padding:'6px', borderRadius:'6px', border:'none', background: viewMode==='grid'?'white':'transparent', color: viewMode==='grid'?'#2563eb':'#64748b', cursor:'pointer' }}
                >
                  <Grid size={18}/>
                </button>
                <button 
                  onClick={() => setViewMode('list')}
                  style={{ padding:'6px', borderRadius:'6px', border:'none', background: viewMode==='list'?'white':'transparent', color: viewMode==='list'?'#2563eb':'#64748b', cursor:'pointer' }}
                >
                  <List size={18}/>
                </button>
             </div>
             <Button onClick={() => setIsModalOpen(true)}>
                <Plus size={16} className="mr-2" /> New Project
             </Button>
          </div>
       </div>

       <div style={viewMode === 'grid' ? gridStyle : listStyle}>
          {projects?.map(project => (
             <ProjectCard 
                key={project.id} 
                project={project} 
                onClick={() => navigate(`/projects/${project.id}`)}
             />
          ))}
          {!projects?.length && (
              <div style={{gridColumn:'1/-1', textAlign:'center', padding:'4rem', border:'2px dashed #e2e8f0', borderRadius:'16px', color:'#9ca3af'}}>
                  <FolderPlus size={48} style={{margin:'0 auto 1rem auto', opacity:0.3}} />
                  <p>No projects found in this workspace.</p>
              </div>
          )}
       </div>

       {isModalOpen && <CreateProjectModal onClose={() => setIsModalOpen(false)} />}
    </div>
  );
};

export default WorkspaceProjectsList;