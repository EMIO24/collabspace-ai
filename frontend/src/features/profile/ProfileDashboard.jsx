import React from 'react';
import { motion } from 'framer-motion';
import StatsGrid from './StatsGrid';
import ActivityHeatmap from './ActivityHeatmap';
import StatusWidget from './StatusWidget';
import Avatar from '../../components/ui/Avatar/Avatar';

const ProfileDashboard = () => {
  return (
    <div className="max-w-6xl mx-auto pb-10">
      {/* Header Section */}
      <div className="flex items-center gap-6 mb-8">
        <Avatar size="lg" className="h-24 w-24 border-4 border-white shadow-xl" />
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Welcome back, Engineer</h1>
          <p className="text-gray-500">Manage your projects and track your productivity.</p>
        </div>
      </div>

      <StatusWidget />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <StatsGrid />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        <ActivityHeatmap />
      </motion.div>
    </div>
  );
};

export default ProfileDashboard;