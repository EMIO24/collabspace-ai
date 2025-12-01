import React, { useState } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import WorkspaceMetrics from '../features/analytics/WorkspaceMetrics';
import BurndownChart from '../features/analytics/BurndownChart';
import TimeReportTable from '../features/analytics/TimeReportTable';

const AnalyticsPage = () => {
  const { currentWorkspace } = useWorkspace();
  // In a real app, you might select a specific project from a dropdown for the burndown
  // For now, we'll assume we pick the first project or pass a null if dashboard is workspace-wide
  const [selectedProjectId, setSelectedProjectId] = useState(null); 

  if (!currentWorkspace) {
    return <div className="p-8 text-center text-gray-500">Please select a workspace.</div>;
  }

  return (
    <div className="max-w-6xl mx-auto pb-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Analytics</h1>
        <p className="text-gray-500">Insights for {currentWorkspace.name}</p>
      </div>

      <WorkspaceMetrics workspaceId={currentWorkspace.id} />

      {/* Logic to select project would go here. 
         For demonstration, we render Burndown only if a project is selected/available 
         or we can pass a 'demo' ID if needed.
      */}
      {selectedProjectId ? (
        <BurndownChart projectId={selectedProjectId} />
      ) : (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8 text-blue-700">
          Select a project to view its Burndown Chart.
        </div>
      )}

      <TimeReportTable workspaceId={currentWorkspace.id} />
    </div>
  );
};

export default AnalyticsPage;