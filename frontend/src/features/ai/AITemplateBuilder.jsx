import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Sparkles, Plus, Play, Save, X, Edit3, Trash2, 
  Terminal, FileText, Calendar, BarChart3, Users 
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Button from '../../components/ui/Button/Button';
import Input from '../../components/ui/Input/Input';
import styles from './AITemplateBuilder.module.css';

const CATEGORIES = [
  { id: 'tasks', label: 'Tasks', color: 'cat_tasks', icon: FileText },
  { id: 'meetings', label: 'Meetings', color: 'cat_meetings', icon: Calendar },
  { id: 'analytics', label: 'Analytics', color: 'cat_analytics', icon: BarChart3 },
  { id: 'reports', label: 'Reports', color: 'cat_reports', icon: Terminal },
];

const VARIABLES = [
  { label: 'Project Name', tag: '{{project}}' },
  { label: 'User Name', tag: '{{user}}' },
  { label: 'Current Date', tag: '{{date}}' },
  { label: 'Task List', tag: '{{tasks}}' },
  { label: 'Team Members', tag: '{{team}}' },
];

const AITemplateBuilder = () => {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);

  // --- DATA FETCHING ---
  const { data: templates, isLoading } = useQuery({
    queryKey: ['aiTemplates'],
    queryFn: async () => {
      try {
        const res = await api.get('/ai/templates/');
        return Array.isArray(res.data) ? res.data : (res.data.results || []);
      } catch {
        // Fallback Mock Data
        return [
          { id: 1, name: 'Sprint Retro', category: 'meetings', use_count: 124, description: 'Summarize sprint outcomes and action items.', prompt_text: 'Analyze these notes...' },
          { id: 2, name: 'Bug Triage', category: 'tasks', use_count: 89, description: 'Categorize and prioritize bug reports.', prompt_text: 'Review the following bugs...' },
        ];
      }
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/ai/templates/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries(['aiTemplates']);
      toast.success('Template deleted');
    }
  });

  // --- HANDLERS ---
  const handleEdit = (template) => {
    setEditingTemplate(template);
    setIsModalOpen(true);
  };

  const handleCreate = () => {
    setEditingTemplate(null);
    setIsModalOpen(true);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.title}>
          <h1><Sparkles className="text-purple-600" /> AI Template Builder</h1>
          <p className={styles.subtitle}>Create and manage custom AI prompts for your team.</p>
        </div>
        <Button onClick={handleCreate} className="bg-purple-600 hover:bg-purple-700 text-white">
          <Plus size={18} className="mr-2" /> Create Template
        </Button>
      </div>

      {isLoading ? (
        <div className="p-10 text-center text-gray-500">Loading templates...</div>
      ) : (
        <div className={styles.grid}>
          {templates.map(template => {
            const category = CATEGORIES.find(c => c.id === template.category) || CATEGORIES[0];
            const Icon = category.icon;
            
            return (
              <div key={template.id} className={styles.card}>
                <div className={styles.cardHeader}>
                  <div className={`p-3 rounded-xl bg-gray-50 text-gray-600`}>
                    <Icon size={24} />
                  </div>
                  <span className={`${styles.categoryBadge} ${styles[category.color]}`}>
                    {category.label}
                  </span>
                </div>
                
                <h3 className={styles.cardTitle}>{template.name}</h3>
                <p className={styles.cardDesc}>{template.description}</p>
                
                <div className={styles.cardFooter}>
                  <span className={styles.useCount}>
                    <Play size={14} /> Used {template.use_count} times
                  </span>
                  <div className="flex gap-2">
                    <button className="p-2 text-gray-400 hover:text-blue-600 transition-colors" onClick={() => handleEdit(template)}>
                      <Edit3 size={16} />
                    </button>
                    <button className="p-2 text-gray-400 hover:text-red-500 transition-colors" onClick={() => deleteMutation.mutate(template.id)}>
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                
                <div className="mt-4 pt-4 border-t border-gray-100">
                   <Button variant="ghost" className="w-full justify-center border border-gray-200">
                     Use Template
                   </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {isModalOpen && (
        <TemplateEditorModal 
          initialData={editingTemplate} 
          onClose={() => setIsModalOpen(false)} 
        />
      )}
    </div>
  );
};

// --- SUB-COMPONENT: EDITOR MODAL ---
const TemplateEditorModal = ({ initialData, onClose }) => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    name: initialData?.name || '',
    category: initialData?.category || 'tasks',
    description: initialData?.description || '',
    prompt_text: initialData?.prompt_text || ''
  });
  
  // Test State
  const [testVariables, setTestVariables] = useState({});
  const [previewOutput, setPreviewOutput] = useState('');

  const saveMutation = useMutation({
    mutationFn: (data) => {
      return initialData 
        ? api.put(`/ai/templates/${initialData.id}/`, data)
        : api.post('/ai/templates/', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['aiTemplates']);
      toast.success(initialData ? 'Template updated' : 'Template created');
      onClose();
    }
  });

  const insertVariable = (tag) => {
    setFormData(prev => ({ ...prev, prompt_text: prev.prompt_text + ` ${tag} ` }));
  };

  const runTest = () => {
    // Mock AI Generation for preview
    let output = formData.prompt_text;
    Object.keys(testVariables).forEach(key => {
       output = output.replace(new RegExp(`{{${key}}}`, 'g'), testVariables[key] || `[${key}]`);
    });
    setPreviewOutput(`[AI Simulation]: Based on your prompt...\n\n${output}\n\nThis is a generated response preview.`);
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h2 className="text-xl font-bold text-gray-800">
            {initialData ? 'Edit Template' : 'Create AI Template'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={24} />
          </button>
        </div>

        <div className={styles.modalBody}>
          {/* Left: Editor */}
          <div className={styles.editorCol}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Template Name</label>
              <input 
                className={styles.input} 
                value={formData.name}
                onChange={e => setFormData({...formData, name: e.target.value})}
                placeholder="e.g. Weekly Report Generator"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className={styles.label}>Category</label>
                <select 
                  className={styles.input}
                  value={formData.category}
                  onChange={e => setFormData({...formData, category: e.target.value})}
                >
                  {CATEGORIES.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
                </select>
              </div>
            </div>

            <div className={styles.formGroup}>
               <label className={styles.label}>Prompt Engineering</label>
               <div className={styles.varToolbar}>
                  {VARIABLES.map(v => (
                    <button key={v.tag} className={styles.varBtn} onClick={() => insertVariable(v.tag)}>
                       + {v.label}
                    </button>
                  ))}
               </div>
               <textarea 
                 className={styles.promptEditor}
                 value={formData.prompt_text}
                 onChange={e => setFormData({...formData, prompt_text: e.target.value})}
                 placeholder="You are a helpful project manager. Please summarize {{project}}..."
               />
            </div>
          </div>

          {/* Right: Test & Preview */}
          <div className={styles.previewCol}>
             <h3 className="font-bold text-gray-700 mb-4">Test Playground</h3>
             <div className={styles.testPanel}>
                <div className="space-y-3 mb-4">
                   {VARIABLES.map(v => {
                      const key = v.tag.replace(/{{|}}/g, '');
                      return (
                        <div key={key}>
                           <label className="text-xs font-semibold text-gray-500 uppercase">{v.label}</label>
                           <input 
                             className={styles.input} 
                             style={{padding: '0.4rem', fontSize: '0.85rem'}}
                             placeholder={`Value for ${v.tag}`}
                             onChange={e => setTestVariables({...testVariables, [key]: e.target.value})}
                           />
                        </div>
                      );
                   })}
                </div>
                <Button onClick={runTest} className="w-full bg-indigo-600 text-white">
                   <Play size={16} className="mr-2" /> Run Test
                </Button>

                {previewOutput && (
                   <div className={styles.previewOutput}>
                      {previewOutput}
                   </div>
                )}
             </div>
          </div>
        </div>

        <div className={styles.modalFooter}>
           <Button variant="ghost" onClick={onClose}>Cancel</Button>
           <Button onClick={() => saveMutation.mutate(formData)} isLoading={saveMutation.isPending}>
              Save Template
           </Button>
        </div>
      </div>
    </div>
  );
};

export default AITemplateBuilder;