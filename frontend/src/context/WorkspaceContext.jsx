import React, { createContext, useContext, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

const WorkspaceContext = createContext();

export const useWorkspace = () => useContext(WorkspaceContext);

export const WorkspaceProvider = ({ children }) => {
  const [currentWorkspace, setCurrentWorkspace] = useState(null);

  // Fetch workspaces list
  const { data: workspaces, isLoading, refetch } = useQuery({
    queryKey: ['workspaces'],
    queryFn: async () => {
      const res = await api.get('/workspaces/');
      return res.data;
    },
    onSuccess: (data) => {
      // Auto-select first workspace if none selected
      if (!currentWorkspace && data && data.length > 0) {
        setCurrentWorkspace(data[0]);
      }
    }
  });

  return (
    <WorkspaceContext.Provider value={{ 
      currentWorkspace, 
      setCurrentWorkspace, 
      workspaces: workspaces || [],
      isLoading,
      refetchWorkspaces: refetch
    }}>
      {children}
    </WorkspaceContext.Provider>
  );
};