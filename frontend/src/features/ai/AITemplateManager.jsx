import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Sparkles, Trash2, Plus } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Button from '../../components/ui/Button/Button';
import styles from './AITemplateManager.module.css';

const AITemplateManager = () => {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({ name: '', prompt_text: '' });

  const { data: templates, isLoading } = useQuery({
    queryKey: ['aiTemplates'],
    queryFn: async () => (await api.get('/ai/templates/')).data
  });

  const mutation = useMutation({
    mutationFn: (data) => api.post('/ai/templates/', data),
    onSuccess: () => {
      queryClient.invalidateQueries(['aiTemplates']);
      toast.success('Template saved');
      setIsEditing(false);
      setFormData({ name: '', prompt_text: '' });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/ai/templates/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries(['aiTemplates']);
      toast.success('Template deleted');
    }
  });

  return (
    <div>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>AI Templates</h2>
          <p className={styles.subtitle}>Customize the prompts used by CollabAI.</p>
        </div>
        <Button onClick={() => setIsEditing(true)}>
          <Plus size={16} style={{ marginRight: '8px' }} /> New Prompt
        </Button>
      </div>

      {isEditing && (
        <div className={styles.editor}>
          <div className={styles.formStack}>
            <input 
              className={styles.input} 
              placeholder="Template Name (e.g., Bug Report Analysis)"
              value={formData.name}
              onChange={e => setFormData({...formData, name: e.target.value})}
            />
            <textarea 
              className={styles.textarea} 
              placeholder="Enter your system prompt here..."
              value={formData.prompt_text}
              onChange={e => setFormData({...formData, prompt_text: e.target.value})}
            />
            <div className={styles.editorActions}>
              <Button variant="ghost" onClick={() => setIsEditing(false)}>Cancel</Button>
              <Button onClick={() => mutation.mutate(formData)}>Save Template</Button>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div>Loading templates...</div>
      ) : (
        <div className={styles.grid}>
          {templates?.map((t) => (
            <div key={t.id} className={styles.card}>
              <div style={{ flex: 1 }}>
                <div className={styles.cardHeader}>
                  <Sparkles size={14} className={styles.cardIcon} />
                  <h4 className={styles.cardTitle}>{t.name}</h4>
                </div>
                <p className={styles.cardPrompt}>{t.prompt_text}</p>
              </div>
              <button 
                onClick={() => deleteMutation.mutate(t.id)}
                className={styles.deleteBtn}
                title="Delete Template"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AITemplateManager;