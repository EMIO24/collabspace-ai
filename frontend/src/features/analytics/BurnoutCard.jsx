import React, { useEffect, useState } from 'react';
import { aiService } from '../../services/aiService';
import styles from './AnalyticsComponents.module.css';

const BurnoutCard = ({ projectId }) => {
  const [risks, setRisks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      setIsLoading(true);
      const res = await aiService.getBurnoutRisks(projectId);
      
      if (isMounted) {
        // Handle response structure variations
        const riskData = Array.isArray(res) ? res : (res?.burnout_risks || []);
        setRisks(riskData);
        setIsLoading(false);
      }
    };

    if (projectId) fetchData();

    return () => { isMounted = false; };
  }, [projectId]);

  const getBadgeClass = (status) => {
    const s = (status || '').toUpperCase();
    if (s === 'RED' || s === 'HIGH') return styles.badgeRed;
    if (s === 'YELLOW' || s === 'MEDIUM') return styles.badgeYellow;
    return styles.badgeGreen;
  };

  if (isLoading) {
    return (
      <div className={styles.card}>
        <h3 className={styles.title} style={{ color: '#ef4444' }}>⚠️ Burnout Risks</h3>
        <div className={styles.loading}>Analyzing workload...</div>
      </div>
    );
  }

  return (
    <div className={styles.card}>
      <h3 className={styles.title} style={{ color: '#ef4444' }}>⚠️ Burnout Risks</h3>
      <div className={styles.riskList}>
        {risks.length > 0 ? (
          risks.map((risk, idx) => (
            <div key={idx} className={styles.riskItem}>
              <div className={styles.userInfo}>
                <div className={styles.avatar}>
                  {risk.user?.username?.[0]?.toUpperCase() || 'U'}
                </div>
                <div className={styles.userDetails}>
                  <p className={styles.userName}>{risk.user?.username || 'Unknown User'}</p>
                  <p className={styles.workload}>
                    {risk.workload_hours || 0}h / {risk.capacity_hours || 40}h capacity
                  </p>
                </div>
              </div>
              
              <span className={`${styles.badge} ${getBadgeClass(risk.status)}`}>
                {risk.status || 'UNKNOWN'}
              </span>
            </div>
          ))
        ) : (
          <p className={styles.emptyState}>No immediate burnout risks detected.</p>
        )}
      </div>
    </div>
  );
};

export default BurnoutCard;