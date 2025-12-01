import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import { MessageSquare, Zap } from 'lucide-react';
import { toast } from 'react-hot-toast';
import Card from '../../components/ui/Card/Card';
import Button from '../../components/ui/Button/Button';
import Input from '../../components/ui/Input/Input';

const StatusWidget = () => {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState('online');
  const [message, setMessage] = useState('');

  const mutation = useMutation({
    mutationFn: (payload) => api.post('/auth/activity/update/', payload),
    onSuccess: () => {
      toast.success('Status updated');
      queryClient.invalidateQueries(['userProfile']);
      setMessage('');
    },
    onError: () => toast.error('Failed to update status')
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate({ status, message });
  };

  return (
    <div className="sticky top-20 z-10 mb-8">
      <Card className="p-4 flex items-center gap-4 bg-white/80 backdrop-blur-xl border-white/50 shadow-lg">
        <div className="flex-shrink-0 p-2 bg-blue-100 text-blue-600 rounded-full">
          <Zap size={20} />
        </div>
        
        <form onSubmit={handleSubmit} className="flex-1 flex gap-4 items-center">
          <select 
            value={status} 
            onChange={(e) => setStatus(e.target.value)}
            className="bg-transparent border-none text-sm font-semibold text-gray-700 focus:ring-0 cursor-pointer"
          >
            <option value="online">🟢 Online</option>
            <option value="focus">🟣 Focusing</option>
            <option value="away">🟡 Away</option>
            <option value="offline">⚪ Offline</option>
          </select>

          <div className="h-6 w-px bg-gray-300" />

          <input
            type="text"
            placeholder="What are you working on?"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="flex-1 bg-transparent border-none focus:ring-0 text-sm text-gray-600 placeholder-gray-400"
          />

          <Button size="sm" type="submit" isLoading={mutation.isPending} variant="ghost" className="!p-2">
            <MessageSquare size={18} />
          </Button>
        </form>
      </Card>
    </div>
  );
};

export default StatusWidget;