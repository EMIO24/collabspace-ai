import React, { createContext, useContext, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

const WorkspaceContext = createContext();

export const useWorkspace = () => useContext(WorkspaceContext);

export const WorkspaceProvider = ({ children }) => {
  const [currentWorkspace, setCurrentWorkspace] = useState(null);

  // Fetch workspaces list
  const { data: rawData, isLoading, refetch } = useQuery({
    queryKey: ['workspaces'],
    queryFn: async () => {
      const res = await api.get('/workspaces/');
      return res.data;
    }
  });

  // SAFETY CHECK: Normalize data to ensure it is always an array
  // Handles cases where API returns { results: [...] } (Pagination) or just [...]
  const workspaces = React.useMemo(() => {
    if (!rawData) return [];
    if (Array.isArray(rawData)) return rawData;
    if (rawData.results && Array.isArray(rawData.results)) return rawData.results;
    return [];
  }, [rawData]);

  // Effect to auto-select the first workspace when data loads
  useEffect(() => {
    if (!currentWorkspace && workspaces.length > 0) {
      setCurrentWorkspace(workspaces[0]);
    }
  }, [workspaces, currentWorkspace]);

  return (
    <WorkspaceContext.Provider value={{ 
      currentWorkspace, 
      setCurrentWorkspace, 
      workspaces, 
      isLoading,
      refetchWorkspaces: refetch
    }}>
      {children}
    </WorkspaceContext.Provider>
  );
};