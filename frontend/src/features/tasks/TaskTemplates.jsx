import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Copy } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Button from '../../components/ui/Button/Button';
import Input from '../../components/ui/Input/Input';
import styles from './TaskTemplates.module.css';

const TaskTemplates = () => {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({ title: '', priority: 'medium', description: '' });

  // --- FETCH TEMPLATES ---
  const { data: templates, isLoading } = useQuery({
    queryKey: ['taskTemplates'],
    queryFn: async () => {
      const res = await api.get('/tasks/templates/');
      return res.data;
    }
  });

  // --- CREATE TEMPLATE ---
  const mutation = useMutation({
    mutationFn: (data) => api.post('/tasks/templates/', data),
    onSuccess: () => {
      queryClient.invalidateQueries(['taskTemplates']);
      toast.success('Template created');
      setIsModalOpen(false);
      setFormData({ title: '', priority: 'medium', description: '' });
    },
    onError: () => toast.error('Failed to create template')
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Task Templates</h1>
          <p className={styles.subtitle}>Standardize your workflow with reusable task structures.</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus size={18} className="mr-2" /> New Template
        </Button>
      </div>

      {isLoading ? (
        <div>Loading templates...</div>
      ) : (
        <div className={styles.grid}>
          {templates?.map(template => (
            <div key={template.id} className={styles.card}>
              <div className={styles.cardHeader}>
                <h3 className={styles.cardTitle}>{template.title}</h3>
                <span className={styles.priorityBadge}>{template.priority}</span>
              </div>
              <p className={styles.description}>
                {template.description || 'No description provided.'}
              </p>
              <div className={styles.footer}>
                <Button variant="ghost" size="sm" onClick={() => toast.success('Applied template (Mock)')}>
                  <Copy size={14} className="mr-2" /> Use Template
                </Button>
              </div>
            </div>
          ))}
          {!templates?.length && (
            <div className="col-span-full text-center text-gray-400 py-10">
              No templates found. Create one to get started.
            </div>
          )}
        </div>
      )}

      {isModalOpen && (
        <div className={styles.overlay} onClick={() => setIsModalOpen(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <h2 style={{ marginBottom: '1.5rem', fontWeight: 700 }}>Create Template</h2>
            <form onSubmit={handleSubmit} className={styles.form}>
              <Input 
                label="Template Name"
                value={formData.title}
                onChange={e => setFormData({...formData, title: e.target.value})}
                required
              />
              <div>
                <label className="block text-sm font-semibold mb-1 text-gray-700">Priority</label>
                <select 
                  className="w-full p-2 border rounded-lg bg-white"
                  value={formData.priority}
                  onChange={e => setFormData({...formData, priority: e.target.value})}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1 text-gray-700">Description</label>
                <textarea 
                  className="w-full p-2 border rounded-lg bg-white"
                  rows={3}
                  value={formData.description}
                  onChange={e => setFormData({...formData, description: e.target.value})}
                />
              </div>
              <div className="flex justify-end gap-2 mt-4">
                <Button variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                <Button type="submit" isLoading={mutation.isPending}>Create</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskTemplates;