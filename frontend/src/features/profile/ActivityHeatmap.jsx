import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import Card from '../../components/ui/Card/Card';
import styles from './ActivityHeatmap.module.css';

const ActivityHeatmap = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['userProfile'],
    queryFn: async () => {
      const res = await api.get('/auth/profile/');
      return res.data; // Expecting { activity_log: { "2023-10-01": 5, ... } }
    }
  });

  // Generate last 365 days
  const calendarData = useMemo(() => {
    const days = [];
    const today = new Date();
    const activityMap = data?.activity_log || {};

    for (let i = 364; i >= 0; i--) {
      const d = new Date();
      d.setDate(today.getDate() - i);
      const dateStr = d.toISOString().split('T')[0];
      const count = activityMap[dateStr] || 0;
      
      let level = 'level0';
      if (count > 0) level = 'level1';
      if (count >= 3) level = 'level2';
      if (count >= 6) level = 'level3';
      if (count >= 10) level = 'level4';

      days.push({ date: dateStr, count, level });
    }
    return days;
  }, [data]);

  if (isLoading) return <Card className="h-64 animate-pulse bg-white/30" />;

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Contribution Activity</h3>
      <div className="w-full overflow-x-auto pb-2">
        {/* Simplified grid layout using Flex for wrapping behavior similar to contrib graph */}
        <div className="flex flex-wrap gap-1 max-w-full justify-start content-start">
          {calendarData.map((day) => (
            <div
              key={day.date}
              title={`${day.date}: ${day.count} contributions`}
              className={`${styles.day} ${styles[day.level]}`}
            />
          ))}
        </div>
      </div>
      <div className="flex items-center gap-2 mt-4 text-xs text-gray-500 justify-end">
        <span>Less</span>
        <div className={`${styles.day} ${styles.level0}`} />
        <div className={`${styles.day} ${styles.level1}`} />
        <div className={`${styles.day} ${styles.level2}`} />
        <div className={`${styles.day} ${styles.level3}`} />
        <div className={`${styles.day} ${styles.level4}`} />
        <span>More</span>
      </div>
    </Card>
  );
};

export default ActivityHeatmap;